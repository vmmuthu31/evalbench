#!/usr/bin/env python3
"""Canonical bootstrap procedure for every confidence interval reported in the EvalBench v1 manuscript.

Procedure (one rule for all analyses):
  * records are sorted by record_id before resampling, so the result does not depend on file order;
  * numpy.random.default_rng(42), B = 10,000 resamples, each resample = rng.integers(0, n, n) (percentile method);
  * the 2.5th and 97.5th percentiles are taken over resamples where the statistic is defined (np.nanpercentile);
    a resample in which AUROC or Pearson r is undefined (single class / constant input) is skipped;
  * AUROC uses mid-ranks for tied confidences; ECE uses 10 equal-width bins; correctness = |pred - true| <= tol marks;
  * Track 1 gaps: IAM and IIIT-Word are independent samples, so each resample draws the IAM indices and then the
    IIIT-Word indices from the same generator; permutation p-values use rng = default_rng(42), 10,000 shuffles of the
    pooled indicators, p = (count + 1) / (B + 1).
Run from the repository root:  python3 scripts/experiments/canonical_bootstrap.py
Writes outputs/experiments/bootstrap_canonical.csv (every interval used in the paper).
"""
import json, csv, collections
import numpy as np
from scipy.stats import rankdata, spearmanr

O = "outputs/experiments/"; B = 10000
load = lambda p: sorted((json.loads(l) for l in open(O + p)), key=lambda r: r["record_id"])

def boot(stat, n, B=B):
    rng = np.random.default_rng(42); v = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        try: v.append(stat(i))
        except Exception: v.append(np.nan)
    v = np.array(v, float); return tuple(np.nanpercentile(v, [2.5, 97.5]))

def pearson(a, b):
    if a.std() == 0 or b.std() == 0: return np.nan
    return float(np.corrcoef(a, b)[0, 1])

def auroc(c, y):
    y = np.asarray(y, int); p = y.sum(); n = len(y) - p
    if p == 0 or n == 0: return np.nan
    r = rankdata(np.asarray(c, float)); return (r[y == 1].sum() - p * (p + 1) / 2) / (p * n)

def ece(c, y, b=10):
    c = np.asarray(c, float); y = np.asarray(y, float); k = np.minimum((c * b).astype(int), b - 1)
    return sum((k == i).mean() * abs(y[k == i].mean() - c[k == i].mean()) for i in range(b) if (k == i).any())

def brier(c, y): return float(((np.asarray(c, float) - np.asarray(y, float)) ** 2).mean())

def main():
    rows = []
    def add(group, metric, est, ci): rows.append([group, metric, round(float(est), 3), round(ci[0], 3), round(ci[1], 3)])
    # Track 1 gaps
    R = [r for r in load("ocr/predictions.jsonl") + load("ocr/ocrspace_engine2_predictions.jsonl") if r["dataset"] in ("iam", "iiit_word")]
    models = ["tesseract5", "easyocr", "trocr_base", "paddleocr", "ocrspace_e2"]
    by = collections.defaultdict(dict)
    for r in R:
        if len(r["ref"].strip()) >= 3: by[(r["model"], r["dataset"])][r["record_id"]] = r
    ids = {}
    for ds in ("iam", "iiit_word"):
        s = set(by[(models[0], ds)])
        for m in models[1:]: s &= set(by[(m, ds)])
        ids[ds] = sorted(s)
    for m in models:
        a = np.array([by[(m, "iam")][i]["exact_match"] for i in ids["iam"]]); b = np.array([by[(m, "iiit_word")][i]["exact_match"] for i in ids["iiit_word"]])
        gap = a.mean() - b.mean(); rng = np.random.default_rng(42); g = []
        for _ in range(B):
            ia = rng.integers(0, len(a), len(a)); ib = rng.integers(0, len(b), len(b)); g.append(a[ia].mean() - b[ib].mean())
        add(f"T1 {m}", "EM gap IAM-IIIT", gap, np.percentile(g, [2.5, 97.5]))
        pool = np.concatenate([a, b]); rng = np.random.default_rng(42); cnt = 0
        for _ in range(B):
            p = rng.permutation(pool); cnt += abs(p[:len(a)].mean() - p[len(a):].mean()) >= abs(gap)
        rows.append([f"T1 {m}", "permutation p", round((cnt + 1) / (B + 1), 4), "", ""])
    # Track 2
    T = load("track2/track2_predictions.jsonl"); F = load("track2/track2_florence2_predictions.jsonl"); fid = {r["record_id"] for r in F}
    for name, rr in (("tesseract5", [r for r in T if r["record_id"] in fid]), ("florence2-base", F)):
        c = np.array([r["cer"] for r in rr]); ca = np.maximum(0, 1 - c); n = len(c)
        add(f"T2 {name}", "CER", c.mean(), boot(lambda i: c[i].mean(), n)); add(f"T2 {name}", "CharAcc", ca.mean(), boot(lambda i: ca[i].mean(), n))
    # Tracks 3 and 5
    for run, d in (("Run 1", "fixed_model"), ("Run 2", "fixed_model_rep2")):
        t3 = load(f"{d}/track3_predictions.jsonl"); t5 = load(f"{d}/track5_predictions.jsonl")
        tr = np.array([x["true_score"] for x in t3], float); pr = np.array([x["pred_score"] for x in t3], float); e = abs(pr - tr); n = len(e)
        add(f"T3 {run}", "MAE", e.mean(), boot(lambda i: e[i].mean(), n))
        add(f"T3 {run}", "Pearson r", pearson(pr, tr), boot(lambda i: pearson(pr[i], tr[i]), n))
        add(f"T3 {run}", "Spearman rho", spearmanr(pr, tr)[0], boot(lambda i: spearmanr(pr[i], tr[i])[0], n))
        sc = np.array([x["pred_score"] for x in t5], float); tt = np.array([x["true_score"] for x in t5], float); cf = np.array([x["confidence"] for x in t5], float)
        for tol in (1, 2, 3, 5, 10):
            y = (abs(sc - tt) <= tol).astype(int)
            add(f"T5 {run} tol {tol}", "AUROC", auroc(cf, y), boot(lambda i: auroc(cf[i], y[i]), len(y)))
            add(f"T5 {run} tol {tol}", "ECE", ece(cf, y), boot(lambda i: ece(cf[i], y[i]), len(y)))
            add(f"T5 {run} tol {tol}", "Brier", brier(cf, y), boot(lambda i: brier(cf[i], y[i]), len(y)))
    # earlier mixed-version run
    t3 = load("track3/track3_predictions.jsonl"); t5 = load("track5/track5_predictions.jsonl")
    tr = np.array([x["true_score"] for x in t3], float); pr = np.array([x["pred_score"] for x in t3], float); e = abs(pr - tr); n = len(e)
    add("T3 mixed", "MAE", e.mean(), boot(lambda i: e[i].mean(), n)); add("T3 mixed", "Pearson r", pearson(pr, tr), boot(lambda i: pearson(pr[i], tr[i]), n))
    sc = np.array([x["pred_score"] for x in t5], float); tt = np.array([x["true_score"] for x in t5], float); cf = np.array([x["confidence"] for x in t5], float); y = (abs(sc - tt) <= 3).astype(int)
    add("T5 mixed tol 3", "AUROC", auroc(cf, y), boot(lambda i: auroc(cf[i], y[i]), len(y))); add("T5 mixed tol 3", "ECE", ece(cf, y), boot(lambda i: ece(cf[i], y[i]), len(y)))
    with open(O + "bootstrap_canonical.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["analysis", "metric", "estimate", "ci_lo", "ci_hi"]); w.writerows(rows)
    for r in rows: print(*r, sep=",")

if __name__ == "__main__":
    main()
