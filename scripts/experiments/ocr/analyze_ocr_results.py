"""
Post-hoc analysis of OCR predictions.jsonl:
- Mean and median CER/WER/EM per model × dataset
- CER distribution plot
- Error analysis: what causes high CER (short words, punctuation, capitalization)

Usage: python3 experiments/ocr/analyze_ocr_results.py
"""

from __future__ import annotations
import json
import csv
import statistics
from pathlib import Path
from collections import defaultdict

ROOT    = Path(__file__).parent.parent.parent
OUT_DIR = ROOT / "outputs/experiments/ocr"


def load_predictions() -> list[dict]:
    with open(OUT_DIR / "predictions.jsonl", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def report(preds: list[dict]) -> None:
    by_model: dict[str, list] = defaultdict(list)
    for p in preds:
        by_model[p["model"]].append(p)

    print("\n" + "=" * 80)
    print("OCR Analysis — Mean vs Median CER")
    print("=" * 80)
    print(f"{'Model':<18} {'Dataset':<10} {'N':>5}  {'Mean CER':>9}  {'Median CER':>11}  {'Mean EM':>8}  {'Mean WER':>9}")
    print("-" * 80)

    summary_rows = []
    for model, recs in sorted(by_model.items()):
        by_ds: dict[str, list] = defaultdict(list)
        for r in recs:
            by_ds[r["dataset"]].append(r)
        for ds, ds_recs in sorted(by_ds.items()):
            cers = [r["cer"] for r in ds_recs]
            wers = [r["wer"] for r in ds_recs]
            ems  = [r["exact_match"] for r in ds_recs]
            mean_cer = statistics.mean(cers)
            med_cer  = statistics.median(cers)
            mean_wer = statistics.mean(wers)
            mean_em  = statistics.mean(ems)
            print(f"{model:<18} {ds:<10} {len(ds_recs):>5}  {mean_cer:>9.4f}  {med_cer:>11.4f}  {mean_em:>8.4f}  {mean_wer:>9.4f}")
            summary_rows.append({
                "model": model, "dataset": ds, "n": len(ds_recs),
                "mean_cer": round(mean_cer, 4), "median_cer": round(med_cer, 4),
                "mean_wer": round(mean_wer, 4), "mean_em": round(mean_em, 4),
                "char_accuracy_mean": round(1 - mean_cer, 4),
                "char_accuracy_median_based": round(1 - med_cer, 4),
            })
    print("=" * 80)

    # write extended CSV
    out = OUT_DIR / "ocr_results_extended.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\n  Written: {out}")

    # Error analysis — what word lengths have highest CER
    print("\n  CER by reference word length:")
    print(f"  {'Ref length':>10}  {'Count':>6}  {'Mean CER':>9}  {'Model':}")
    for model, recs in sorted(by_model.items()):
        by_len: dict[int, list] = defaultdict(list)
        for r in recs:
            by_len[len(r["ref"])].append(r["cer"])
        print(f"\n  [{model}]")
        for length in sorted(by_len.keys())[:10]:
            vals = by_len[length]
            print(f"  {'len=' + str(length):>10}  {len(vals):>6}  {statistics.mean(vals):>9.4f}")

    # Figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        # CER distribution histogram per model
        fig, axes = plt.subplots(1, len(by_model), figsize=(5 * len(by_model), 4), sharey=True)
        if len(by_model) == 1:
            axes = [axes]
        COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
        for ax, (model, recs), color in zip(axes, sorted(by_model.items()), COLORS):
            cers = [r["cer"] for r in recs]
            ax.hist(cers, bins=20, range=(0, 2), color=color, alpha=0.8, edgecolor="white")
            ax.axvline(statistics.mean(cers),   color="red",   linestyle="--", label=f"mean={statistics.mean(cers):.3f}")
            ax.axvline(statistics.median(cers), color="black", linestyle="-",  label=f"median={statistics.median(cers):.3f}")
            ax.set_xlabel("CER")
            ax.set_ylabel("Count")
            ax.set_title(model)
            ax.legend(fontsize=8)
        fig.suptitle("CER Distribution per Model — IAM word-level", y=1.02)
        plt.tight_layout()
        out_fig = OUT_DIR / "cer_distribution.png"
        fig.savefig(out_fig, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Written: {out_fig}")

        # Scatter: ref length vs CER per model
        fig, ax = plt.subplots(figsize=(8, 5))
        for (model, recs), color in zip(sorted(by_model.items()), COLORS):
            x = [len(r["ref"]) for r in recs]
            y = [r["cer"]      for r in recs]
            ax.scatter(x, y, alpha=0.15, s=8, color=color, label=model)
            # mean per length
            by_len = defaultdict(list)
            for xi, yi in zip(x, y):
                by_len[xi].append(yi)
            xs_m = sorted(by_len.keys())
            ys_m = [statistics.mean(by_len[xl]) for xl in xs_m]
            ax.plot(xs_m, ys_m, color=color, linewidth=2)
        ax.set_xlabel("Reference word length (characters)")
        ax.set_ylabel("CER")
        ax.set_title("CER vs Reference Word Length — IAM word-level")
        ax.legend()
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 2)
        plt.tight_layout()
        out_fig2 = OUT_DIR / "cer_vs_word_length.png"
        fig.savefig(out_fig2, dpi=150)
        plt.close()
        print(f"  Written: {out_fig2}")

    except ImportError:
        print("  matplotlib not installed — skipping figures")


if __name__ == "__main__":
    preds = load_predictions()
    print(f"Loaded {len(preds):,} predictions")
    report(preds)
