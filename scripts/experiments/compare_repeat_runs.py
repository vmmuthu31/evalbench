"""Compare two fixed-model runs (run 1: outputs/experiments/fixed_model, run 2: fixed_model_rep2).
Usage: python3 experiments/compare_repeat_runs.py   -> writes outputs/experiments/fixed_model_rep2/repeat_comparison.csv"""
import json, sys, importlib.util, csv
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr, spearmanr
ROOT = Path(__file__).parent.parent; EX = ROOT / "outputs/experiments"
s = importlib.util.spec_from_file_location("t5", ROOT / "experiments/track5_trust/run_trust_eval.py"); t5 = importlib.util.module_from_spec(s); s.loader.exec_module(t5)
ld = lambda p: {j["record_id"]: j for j in map(json.loads, open(p)) if j.get("pred_score") is not None}
rows = []
def mae(d): return float(np.mean([abs(j["pred_score"] - j["true_score"]) for j in d.values()]))
def r_(d): return float(pearsonr([j["pred_score"] for j in d.values()], [j["true_score"] for j in d.values()])[0])
def w(d, k): return float(np.mean([abs(j["pred_score"] - j["true_score"]) <= k for j in d.values()]))
for tr in ("track3", "track5"):
    a, b = ld(EX / f"fixed_model/{tr}_predictions.jsonl"), ld(EX / f"fixed_model_rep2/{tr}_predictions.jsonl")
    ids = sorted(set(a) & set(b)); a = {i: a[i] for i in ids}; b = {i: b[i] for i in ids}
    pa, pb = np.array([a[i]["pred_score"] for i in ids]), np.array([b[i]["pred_score"] for i in ids])
    d = pa - pb
    row = {"track": tr, "n": len(ids), "run1_MAE": mae(a), "run2_MAE": mae(b), "run1_r": r_(a), "run2_r": r_(b),
           "run1_within1": w(a, 1), "run2_within1": w(b, 1), "run1_within3": w(a, 3), "run2_within3": w(b, 3),
           "exact_agreement": float(np.mean(d == 0)), "within1_agreement": float(np.mean(abs(d) <= 1)),
           "mean_abs_diff": float(np.mean(abs(d))), "max_abs_diff": float(abs(d).max()), "pearson_between_runs": float(pearsonr(pa, pb)[0])}
    if tr == "track5":
        for k, x in (("run1", a), ("run2", b)):
            m = t5.compute_trust_metrics(list(x.values()))
            for q in ("ece", "auroc", "brier", "accuracy_pm3"): row[f"{k}_{q}"] = m.get(q)
        ca, cb = [a[i]["confidence"] for i in ids], [b[i]["confidence"] for i in ids]
        row["conf_exact_agreement"] = float(np.mean(np.array(ca) == np.array(cb)))
        row["conf_spearman_between_runs"] = float(spearmanr(ca, cb)[0]) if len(set(ca)) > 1 and len(set(cb)) > 1 else None
    rows.append(row)
keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "track", k))
with open(EX / "fixed_model_rep2/repeat_comparison.csv", "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(rows)
for r in rows: print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
