"""Track 3 summary with bootstrap 95% CIs (10,000 resamples, seed 42) from a predictions file.
Usage: python3 experiments/track3_bootstrap_stats.py <track3_predictions.jsonl> <out.csv> [label]"""
import sys, json, csv
import numpy as np
from scipy.stats import pearsonr, spearmanr
pred, out = sys.argv[1], sys.argv[2]; label = sys.argv[3] if len(sys.argv) > 3 else "run"
R = sorted((r for r in map(json.loads, open(pred)) if r.get("pred_score") is not None), key=lambda r: r["record_id"])  # canonical order (see canonical_bootstrap.py)
t = np.array([r["true_score"] for r in R]); p = np.array([r["pred_score"] for r in R]); n = len(R)
def stats(i):
    tt, pp = t[i], p[i]; e = abs(tt - pp)
    return e.mean(), pearsonr(tt, pp)[0], spearmanr(tt, pp)[0]
def pct(v, q):
    v = [x for x in v if x == x]; return float(np.percentile(v, q * 100))
rng = np.random.default_rng(42); bs = [stats(rng.integers(0, n, n)) for _ in range(10000)]
mae, r, rho = stats(np.arange(n)); e = abs(t - p)
row = {"model": label, "n": n, "mae": mae, "mae_lo": pct([b[0] for b in bs], .025), "mae_hi": pct([b[0] for b in bs], .975),
       "pearson_r": r, "pearson_lo": pct([b[1] for b in bs], .025), "pearson_hi": pct([b[1] for b in bs], .975),
       "spearman_rho": rho, "spearman_lo": pct([b[2] for b in bs], .025), "spearman_hi": pct([b[2] for b in bs], .975),
       "within_1": (e <= 1).mean(), "within_3": (e <= 3).mean(), "within_5": (e <= 5).mean(),
       "mean_bias": (p - t).mean(), "median_abs_error": float(np.median(e)), "max_abs_error": e.max(),
       "share_top4_error": float(np.sort(e)[-4:].sum() / e.sum())}
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(row)); w.writeheader(); w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})
print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})
