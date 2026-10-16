#!/usr/bin/env python3
"""Recompute the headline numbers reported in the manuscript from the archived prediction files.

Run from the repository root:  python3 scripts/verify_reported_tables.py
Covers: Track 1 (matched subsets, EM gap, bootstrap CI, permutation p), Track 2 (n = 50),
Track 3 and Track 5 (Run 1 and Run 2). Bootstrap: 10,000 resamples, numpy default_rng(42).
Character accuracy is the per-record max(0, 1 - CER), averaged. (The per-record `char_accuracy` field
stored in older prediction files is the unclamped 1 - CER, so it is recomputed from `cer` here.)
Interval end-points can differ from the manuscript by up to about 0.006 because they depend on the order of records.
"""
import json, collections, numpy as np
from scipy.stats import pearsonr, spearmanr, rankdata

O = "outputs/experiments/"
load = lambda p: [json.loads(l) for l in open(O + p)]

def boot(f, n, B=10000):
    rng = np.random.default_rng(42)
    v = [f(rng.integers(0, n, n)) for _ in range(B)]
    return np.nanpercentile(v, [2.5, 97.5])

def auroc(c, y):
    c = np.asarray(c, float); y = np.asarray(y, int); p = y.sum(); n = len(y) - p
    if p == 0 or n == 0: return np.nan
    r = rankdata(c); return (r[y == 1].sum() - p * (p + 1) / 2) / (p * n)

def ece(c, y, b=10):
    c = np.asarray(c, float); y = np.asarray(y, float); k = np.minimum((c * b).astype(int), b - 1)
    return sum((k == i).mean() * abs(y[k == i].mean() - c[k == i].mean()) for i in range(b) if (k == i).any())

print("== Track 1 (matched subsets, reference length >= 3) ==")
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
print("n IAM", len(ids["iam"]), "n IIIT-Word", len(ids["iiit_word"]))
for m in models:
    o = []
    for ds in ("iam", "iiit_word"):
        rr = [by[(m, ds)][i] for i in ids[ds]]
        o.append((np.mean([x["cer"] for x in rr]), np.array([x["exact_match"] for x in rr]), np.mean([max(0, 1 - x["cer"]) for x in rr])))
    a, b = o[0][1], o[1][1]; gap = a.mean() - b.mean()
    rng = np.random.default_rng(42)
    bs = [a[rng.integers(0, len(a), len(a))].mean() - b[rng.integers(0, len(b), len(b))].mean() for _ in range(10000)]
    lo, hi = np.percentile(bs, [2.5, 97.5]); pool = np.concatenate([a, b]); rng = np.random.default_rng(42); cnt = 0
    for _ in range(10000):
        p = rng.permutation(pool); cnt += abs(p[:len(a)].mean() - p[len(a):].mean()) >= abs(gap)
    print(f"{m:12s} IAM CER {o[0][0]:.3f} EM {a.mean():.3f} CA {o[0][2]:.3f} | IIIT CER {o[1][0]:.3f} EM {b.mean():.3f} CA {o[1][2]:.3f} | gap {gap:+.3f} CI ({lo:+.3f},{hi:+.3f}) p {(cnt + 1) / 10001:.4f}")

print("== Track 2 (50 pages shared by both models) ==")
T = load("track2/track2_predictions.jsonl"); F = load("track2/track2_florence2_predictions.jsonl")
fid = {r["record_id"] for r in F}
for name, rows in (("tesseract5", [r for r in T if r["record_id"] in fid]), ("florence2-base", F)):
    n = len(rows); c = np.array([r["cer"] for r in rows]); w = np.array([r["wer"] for r in rows]); ca = np.maximum(0, 1 - c)
    print(f"{name:15s} n {n} CER {c.mean():.3f} {boot(lambda i: c[i].mean(), n).round(3)} WER {w.mean():.3f} CA {ca.mean():.3f} {boot(lambda i: ca[i].mean(), n).round(3)}")

print("== Tracks 3 and 5, Run 1 and Run 2 ==")
for run, d in (("Run 1", "fixed_model"), ("Run 2", "fixed_model_rep2")):
    t3 = load(f"{d}/track3_predictions.jsonl"); t5 = load(f"{d}/track5_predictions.jsonl")
    tr = np.array([x["true_score"] for x in t3], float); pr = np.array([x["pred_score"] for x in t3], float); e = abs(pr - tr); n = len(e)
    print(f"{run} T3 n {n} MAE {e.mean():.3f} {boot(lambda i: e[i].mean(), n).round(3)} r {pearsonr(pr, tr)[0]:.3f} "
          f"{boot(lambda i: np.corrcoef(pr[i], tr[i])[0, 1], n).round(3)} rho {spearmanr(pr, tr)[0]:.3f} "
          f"EM+-1 {(e <= 1).mean():.3f} EM+-3 {(e <= 3).mean():.3f} EM+-5 {(e <= 5).mean():.3f}")
    sc = np.array([x["pred_score"] for x in t5], float); tt = np.array([x["true_score"] for x in t5], float)
    cf = np.array([x["confidence"] for x in t5], float); y = (abs(sc - tt) <= 3).astype(int)
    print(f"{run} T5 accuracy(+-3) {y.mean():.2f} ECE {ece(cf, y):.3f} AUROC {auroc(cf, y):.3f} "
          f"{boot(lambda i: auroc(cf[i], y[i]), len(y)).round(3)} Brier {((cf - y) ** 2).mean():.3f} MAE {abs(sc - tt).mean():.3f}")
