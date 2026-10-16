"""Track 5 recomputation from raw predictions: per-variant and pooled metrics, and a
correctness-threshold sensitivity table (AUROC, ECE, Brier with bootstrap 95% CIs).
Usage: python track5_sensitivity.py <track5_predictions.jsonl> <out_dir>"""
import sys, json, csv, importlib.util, os
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rte", os.path.join(here, "run_trust_eval.py"))
rte = importlib.util.module_from_spec(spec); spec.loader.exec_module(rte)
pred, out = sys.argv[1], sys.argv[2]
R = [json.loads(l) for l in open(pred)]
R = sorted((r for r in R if r.get("pred_score") is not None and r.get("confidence") is not None), key=lambda r: (r["record_id"], r["model"]))  # canonical order (see canonical_bootstrap.py)
def boot(rs, tol, n=10000, seed=42):
    """Canonical procedure: numpy default_rng(seed), rng.integers(0, len, len) per resample, percentile 2.5/97.5 over defined values."""
    rng = np.random.default_rng(seed); res = []
    for _ in range(n):
        s = [rs[i] for i in rng.integers(0, len(rs), len(rs))]
        m = rte.compute_trust_metrics(s, tol); res.append([np.nan if m[k] is None else m[k] for k in ("auroc", "ece", "brier")])
    res = np.array(res, float)
    return [tuple(np.nanpercentile(res[:, i], [2.5, 97.5])) for i in range(3)]
rows = []
groups = [("pooled", R)] + [(m, [r for r in R if r["model"] == m]) for m in sorted({r["model"] for r in R})]
for name, rs in groups:
    for tol in ([3.0] if name != "pooled" else [1.0, 2.0, 3.0, 5.0, 10.0]):
        m = rte.compute_trust_metrics(rs, tol); ci = boot(rs, tol)
        rows.append({"group": name, "tol_marks": tol, "n": m["n_scored"], "accuracy": m["accuracy_pm3"] if tol == 3 else round(sum(abs(r["true_score"] - r["pred_score"]) <= tol for r in rs) / len(rs), 3),
                     "auroc": m["auroc"], "auroc_lo": round(ci[0][0], 3), "auroc_hi": round(ci[0][1], 3),
                     "ece": m["ece"], "ece_lo": round(ci[1][0], 3), "ece_hi": round(ci[1][1], 3),
                     "brier": m["brier"], "brier_lo": round(ci[2][0], 3), "brier_hi": round(ci[2][1], 3)})
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, "track5_sensitivity.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
