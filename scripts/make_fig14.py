"""Fig. 14: Tesseract page-1 legibility proxy vs |Track-3 grading error| (Mendeley, n=50).
Reads cached Tesseract word output (written by ocr_page1.py) and Track 3 predictions."""
import json, os, sys, csv, numpy as np
from scipy import stats
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS = sys.argv[1]            # dir with w200_<i>.json  (Tesseract image_to_data text/conf)
OUT = sys.argv[2]              # output prefix, e.g. Fig14
PRED = sys.argv[3] if len(sys.argv) > 3 else f"{ROOT}/outputs/experiments/track3/track3_predictions.jsonl"  # fixed-model run: outputs/experiments/fixed_model/track3_predictions.jsonl
pred = {}
for l in open(PRED):
    x = json.loads(l); pred[x["record_id"]] = x
rows = []
for i in range(1, 51):
    w = [(t, c) for t, c in json.load(open(f"{WORDS}/w200_{i}.json")) if t.strip() and c >= 0]
    x = pred[f"MDLY-{i:04d}"]
    rows.append((i, sum(len(t) for t, _ in w), float(np.mean([c for _, c in w])), abs(x["pred_score"] - x["true_score"])))
a = np.array(rows)
rc, pc = stats.pearsonr(a[:, 1], a[:, 3]); rf, pf = stats.pearsonr(a[:, 2], a[:, 3])
sc = stats.spearmanr(a[:, 1], a[:, 3]); sf = stats.spearmanr(a[:, 2], a[:, 3])
print(f"chars r={rc:.3f} p={pc:.3f} | conf r={rf:.3f} p={pf:.3f} | spearman chars {sc[0]:.3f} p={sc[1]:.3f} conf {sf[0]:.3f} p={sf[1]:.3f}")
with open(os.path.join(os.path.dirname(PRED), "cross_track_ocr_legibility.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["script", "page1_chars", "page1_mean_conf", "abs_grading_error"]); wr.writerows(rows)
plt.rcParams.update({"font.family": "Liberation Sans", "pdf.fonttype": 42, "font.size": 8,
                     "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8})
fig, ax = plt.subplots(figsize=(3.4, 2.5))
ax.scatter(a[:, 1], a[:, 3], s=22, color="#4C72B0", alpha=0.7, edgecolor="#1f1f1f", linewidth=0.4)
m, b = np.polyfit(a[:, 1], a[:, 3], 1); xs = np.linspace(a[:, 1].min(), a[:, 1].max(), 50)
ax.plot(xs, m * xs + b, "--", color="#C44E52", lw=1.5)
ax.text(0.03, 0.95, f"r = {rc:.3f}, p = {pc:.3f}, n = 50", transform=ax.transAxes, va="top", fontsize=8,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.5"))
ax.set_xlabel("Page-1 extracted characters (Tesseract proxy)")
ax.set_ylabel("|Grading error| (marks)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT + ".png", dpi=300); fig.savefig(OUT + ".pdf")
