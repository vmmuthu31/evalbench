"""
Generate publication-ready OCR result figures for EvalBench paper.
Reads outputs/experiments/ocr/predictions.jsonl and generates:
  - Figure: grouped bar chart per model × dataset (EM and CER)
  - LaTeX table: word-level results by model and dataset
  - LaTeX table: ablation cross-dataset gap
"""

from __future__ import annotations
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
OUT_DIR = ROOT / "outputs/experiments/ocr"

NICE_NAMES = {
    "tesseract5":  "Tesseract 5",
    "easyocr":     "EasyOCR",
    "trocr_base":  "TrOCR-base",
    "trocr_large": "TrOCR-large",
    "paddleocr":   "PaddleOCR",
    "florence2":   "Florence-2",
}

# word-level models only (page-level handled separately)
WORD_MODELS  = ["tesseract5", "easyocr", "trocr_base", "paddleocr", "florence2"]
WORD_DATASETS = ["iam", "iiit_word"]
COLORS       = ["#937860", "#DD8452", "#4C72B0", "#43A885", "#C44E52"]


def load_predictions(min_ref_len: int = 3) -> list[dict]:
    with open(OUT_DIR / "predictions.jsonl", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()
                if len(json.loads(l).get("ref", "")) >= min_ref_len]


def aggregate_by_model_dataset(preds: list[dict]) -> dict[tuple, dict]:
    """Returns {(model, dataset): metrics_dict}."""
    groups: dict[tuple, list] = defaultdict(list)
    for p in preds:
        groups[(p["model"], p["dataset"])].append(p)

    out = {}
    for (model, dataset), recs in groups.items():
        cers = [r["cer"]         for r in recs]
        ems  = [r["exact_match"] for r in recs]
        lats = [r["latency_ms"]  for r in recs]
        out[(model, dataset)] = {
            "n":          len(recs),
            "mean_cer":   statistics.mean(cers),
            "median_cer": statistics.median(cers),
            "em":         statistics.mean(ems),
            "char_acc":   1 - statistics.mean(cers),
            "ms_img":     statistics.mean(lats),
        }
    return out


def make_multidataset_figure(agg: dict[tuple, dict]) -> None:
    """Grouped bar chart: model × dataset, metric = Exact Match."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    models   = [m for m in WORD_MODELS   if any((m, d) in agg for d in WORD_DATASETS)]
    datasets = [d for d in WORD_DATASETS if any((m, d) in agg for m in WORD_MODELS)]

    ds_labels = {"iam": "IAM", "iiit_word": "IIIT-Word"}
    x = np.arange(len(models))
    w = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(max(10, 2.5*len(models)), 5), sharey=False)

    for ax_idx, (metric, label, ylim) in enumerate([
        ("em",       "Exact Match ↑",       (0, 1.05)),
        ("mean_cer", "Mean CER ↓",           (0, 1.05)),
    ]):
        ax = axes[ax_idx]
        for i, ds in enumerate(datasets):
            offset = (i - (len(datasets)-1)/2) * w
            vals = [agg.get((m, ds), {}).get(metric, 0.0) for m in models]
            bars = ax.bar(x + offset, vals, w,
                          label=ds_labels.get(ds, ds),
                          color=COLORS[i % len(COLORS)],
                          alpha=0.85)
            for bar, v in zip(bars, vals):
                if v > 0.01:
                    ax.text(bar.get_x() + bar.get_width()/2,
                            bar.get_height() + 0.01,
                            f"{v:.2f}", ha="center", va="bottom",
                            fontsize=7.5, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels([NICE_NAMES.get(m, m) for m in models],
                           fontsize=9, rotation=15, ha="right")
        ax.set_ylim(*ylim)
        ax.set_ylabel(label, fontsize=10)
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle("EvalBench OCR Track — Word-level Results by Model and Dataset\n"
                 "(words ≥ 3 chars, n=200–300 per model-dataset pair)", fontsize=11)
    plt.tight_layout()
    out = OUT_DIR / "fig_ocr_multi_dataset.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Written: {out}")


def make_word_level_latex(agg: dict[tuple, dict]) -> None:
    """LaTeX table: OCR word-level results by model × dataset."""
    models   = [m for m in WORD_MODELS   if any((m, d) in agg for d in WORD_DATASETS)]
    datasets = [d for d in WORD_DATASETS if any((m, d) in agg for m in WORD_MODELS)]
    ds_labels = {"iam": "IAM", "iiit_word": "IIIT-Word"}

    # Build column spec: model | (CER, EM) per dataset
    ncols = 1 + 2 * len(datasets)
    col_spec = "l" + "rr" * len(datasets)

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{OCR Track Word-level Results. CER and Exact Match (EM) per model"
                 r" and dataset (words $\geq$ 3 chars, $n$=200 per model-dataset pair).}")
    lines.append(r"\label{tab:ocr_word_results}")
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"\hline")

    # Header row 1: dataset names spanning 2 columns each
    ds_header = " & ".join(
        f"\\multicolumn{{2}}{{c}}{{{ds_labels.get(d, d)}}}" for d in datasets
    )
    lines.append(f"Model & {ds_header} \\\\")

    # Header row 2: metric names
    metric_header = " & ".join(
        r"CER $\downarrow$ & EM $\uparrow$" for _ in datasets
    )
    lines.append(f" & {metric_header} \\\\")
    lines.append(r"\hline")

    for m in models:
        row = [NICE_NAMES.get(m, m)]
        for ds in datasets:
            stats = agg.get((m, ds))
            if stats:
                row.append(f"{stats['mean_cer']:.3f}")
                row.append(f"{stats['em']:.3f}")
            else:
                row.extend(["—", "—"])
        lines.append(" & ".join(row) + r" \\")

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    out = OUT_DIR / "table2_ocr_results.tex"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Written: {out}")
    print("\n--- table2_ocr_results.tex ---")
    print("\n".join(lines))


def make_ablation_latex(agg: dict[tuple, dict]) -> None:
    """LaTeX table: cross-dataset gap (ablation section)."""
    models = [m for m in WORD_MODELS if (m, "iam") in agg and (m, "iiit_word") in agg]

    lines = []
    lines.append(r"\begin{table}[ht]")
    lines.append(r"\centering")
    lines.append(r"\small")
    lines.append(r"\caption{Cross-dataset generalisation gap (Exact Match) for word-level OCR models."
                 r" Positive gap indicates better performance on IAM than IIIT-Word,"
                 r" suggesting IAM-biased training.}")
    lines.append(r"\label{tab:ablation_cross_dataset}")
    lines.append(r"\begin{tabular}{lrrrr}")
    lines.append(r"\hline")
    lines.append(r"Model & IAM EM $\uparrow$ & IIIT-W EM $\uparrow$ & IAM CER $\downarrow$ & Gap (EM) \\")
    lines.append(r"\hline")

    for m in models:
        iam  = agg[(m, "iam")]
        iiit = agg[(m, "iiit_word")]
        gap  = iam["em"] - iiit["em"]
        sign = "+" if gap >= 0 else ""
        lines.append(
            f"{NICE_NAMES.get(m, m)} & {iam['em']:.3f} & {iiit['em']:.3f} "
            f"& {iam['mean_cer']:.3f} & {sign}{gap:.3f} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    out = OUT_DIR / "table_ablation_cross_dataset.tex"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWritten: {out}")
    print("\n--- table_ablation_cross_dataset.tex ---")
    print("\n".join(lines))


def print_summary(agg: dict[tuple, dict]) -> None:
    print("\n" + "=" * 72)
    print("EvalBench OCR — Word-level Results (ref ≥ 3 chars)")
    print("=" * 72)
    print(f"{'Model':<14} {'Dataset':<12} {'N':>5}  {'CER':>7}  {'Median':>7}  {'EM':>6}  {'ms/img':>7}")
    print("-" * 72)
    for m in WORD_MODELS:
        for ds in WORD_DATASETS:
            s = agg.get((m, ds))
            if s:
                print(f"{NICE_NAMES.get(m,m):<14} {ds:<12} {s['n']:>5}  "
                      f"{s['mean_cer']:>7.3f}  {s['median_cer']:>7.3f}  "
                      f"{s['em']:>6.3f}  {s['ms_img']:>7.1f}")
    print("=" * 72)


if __name__ == "__main__":
    preds = load_predictions(min_ref_len=3)
    agg   = aggregate_by_model_dataset(preds)
    print_summary(agg)
    try:
        make_multidataset_figure(agg)
    except ImportError:
        print("matplotlib not installed — skipping figure")
    make_word_level_latex(agg)
    make_ablation_latex(agg)
