"""
EvalBench — Phase 6: OCR Model Evaluation
Evaluates Tesseract, EasyOCR, and TrOCR on Track 1 test records.

Usage:
  python3 experiments/ocr/run_ocr_eval.py                     # all models, 500 samples
  python3 experiments/ocr/run_ocr_eval.py --models tesseract  # single model
  python3 experiments/ocr/run_ocr_eval.py --n 100             # quick smoke test
  python3 experiments/ocr/run_ocr_eval.py --n 0               # full test set

Outputs:
  outputs/experiments/ocr/predictions.jsonl      — per-record predictions
  outputs/experiments/ocr/ocr_results.csv        — aggregate metrics per model x dataset
  outputs/experiments/ocr/ocr_leaderboard.png    — leaderboard figure
"""

from __future__ import annotations
import argparse
import csv
import json
import time
import tracemalloc
from pathlib import Path
from collections import defaultdict

ROOT    = Path(__file__).parent.parent.parent
PROC    = ROOT / "datasets/processed"
OUT_DIR = ROOT / "outputs/experiments/ocr"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── import local metrics ───────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metrics import compute_all


# ── model registry ─────────────────────────────────────────────────────────────
def get_model(name: str):
    from models.tesseract_model  import TesseractModel
    from models.easyocr_model    import EasyOCRModel
    from models.trocr_model      import TrOCRModel
    from models.paddleocr_model  import PaddleOCRModel
    from models.florence2_model  import Florence2Model
    from models.qwen_vl_model    import QwenVLModel

    registry = {
        "tesseract":    lambda: TesseractModel(psm=7),   # word-level
        "tesseract6":   lambda: TesseractModel(psm=6),   # paragraph / page-level
        "easyocr":      lambda: EasyOCRModel(gpu=False),
        "trocr_base":   lambda: TrOCRModel(variant="base"),
        "trocr_large":  lambda: TrOCRModel(variant="large"),
        "paddleocr":    lambda: PaddleOCRModel(lang="en"),
        "florence2":    lambda: Florence2Model(variant="base"),
        "florence2_l":  lambda: Florence2Model(variant="large"),
        "qwen2_5_vl":   lambda: QwenVLModel(),
    }
    if name not in registry:
        raise ValueError(f"Unknown model '{name}'. Available: {list(registry)}")
    return registry[name]()


# ── load test records with OCR ground truth ────────────────────────────────────
def load_test_records(datasets: list[str] | None = None,
                      splits: list[str] | None = None) -> list[dict]:
    """Load records with OCR ground truth from specified splits (default: test)."""
    jsonl = PROC / "evalbench_v1.jsonl"
    allowed_splits = set(splits) if splits else {"test"}
    records = []
    with open(jsonl, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line.strip())
            if r["split"] in allowed_splits and r.get("ocr_text") and r.get("image_path"):
                if datasets is None or r["dataset"] in datasets:
                    records.append(r)
    return records


# ── evaluate one model ─────────────────────────────────────────────────────────
def evaluate_model(model, records: list[dict], n: int) -> list[dict]:
    sample = records if n == 0 else records[:n]
    results = []
    model.load()

    for i, r in enumerate(sample, 1):
        img_path = ROOT / r["image_path"]
        if not img_path.exists():
            continue
        t0 = time.perf_counter()
        tracemalloc.start()
        try:
            pred = model.predict(img_path)
        except Exception as e:
            pred = ""
            print(f"  [warn] {model.name} failed on {r['record_id']}: {e}")
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        latency_ms = (time.perf_counter() - t0) * 1000

        m = compute_all(pred, r["ocr_text"])
        results.append({
            "model":      model.name,
            "record_id":  r["record_id"],
            "dataset":    r["dataset"],
            "pred":       pred,
            "ref":        r["ocr_text"],
            "latency_ms": round(latency_ms, 2),
            "mem_kb":     round(peak / 1024, 1),
            **m,
        })
        if i % 100 == 0:
            avg_cer = sum(x["cer"] for x in results) / len(results)
            print(f"  [{model.name}] {i}/{len(sample)} | avg CER={avg_cer:.3f}")

    model.unload()
    return results


# ── aggregate per model × dataset ─────────────────────────────────────────────
def aggregate(all_results: list[dict]) -> list[dict]:
    groups: dict[tuple, list] = defaultdict(list)
    for r in all_results:
        groups[(r["model"], r["dataset"])].append(r)

    rows = []
    for (model, dataset), recs in sorted(groups.items()):
        n = len(recs)
        rows.append({
            "model":          model,
            "dataset":        dataset,
            "n_samples":      n,
            "cer":            round(sum(r["cer"]           for r in recs) / n, 4),
            "wer":            round(sum(r["wer"]           for r in recs) / n, 4),
            "exact_match":    round(sum(r["exact_match"]   for r in recs) / n, 4),
            "char_accuracy":  round(sum(r["char_accuracy"] for r in recs) / n, 4),
            "latency_ms_avg": round(sum(r["latency_ms"]    for r in recs) / n, 1),
            "mem_kb_peak":    round(max(r["mem_kb"]        for r in recs), 1),
        })
    return rows


# ── write outputs ──────────────────────────────────────────────────────────────
def write_predictions(all_results: list[dict], append: bool = False) -> None:
    out  = OUT_DIR / "predictions.jsonl"
    mode = "a" if append and out.exists() else "w"
    if mode == "a":
        # de-duplicate: don't re-write records already in file
        existing = set()
        with open(out, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                existing.add((r["model"], r["record_id"]))
        new = [r for r in all_results if (r["model"], r["record_id"]) not in existing]
        print(f"\n  Appending {len(new)} new predictions (skipping {len(all_results)-len(new)} duplicates)")
        all_results = new
    with open(out, mode, encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Written: {out}")


def write_csv(rows: list[dict]) -> None:
    out = OUT_DIR / "ocr_results.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {out}")


def write_figure(rows: list[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        models   = sorted(set(r["model"]   for r in rows))
        datasets = sorted(set(r["dataset"] for r in rows))

        # build lookup: (model, dataset) -> char_accuracy
        lookup = {(r["model"], r["dataset"]): r["char_accuracy"] for r in rows}

        x     = np.arange(len(datasets))
        width = 0.8 / max(len(models), 1)
        COLORS = ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B2","#937860"]

        fig, ax = plt.subplots(figsize=(max(8, 3 * len(datasets)), 5))
        for i, model in enumerate(models):
            vals  = [lookup.get((model, ds), 0.0) for ds in datasets]
            bars  = ax.bar(x + i * width, vals, width, label=model, color=COLORS[i % len(COLORS)])
            for bar, v in zip(bars, vals):
                if v > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                            f"{v:.2f}", ha="center", va="bottom", fontsize=7)

        ax.set_xticks(x + width * (len(models) - 1) / 2)
        ax.set_xticklabels(datasets)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Character Accuracy (higher = better)")
        ax.set_title("EvalBench OCR Leaderboard — Character Accuracy by Model & Dataset")
        ax.legend(loc="lower right")
        plt.tight_layout()
        out = OUT_DIR / "ocr_leaderboard.png"
        fig.savefig(out, dpi=150)
        plt.close()
        print(f"  Written: {out}")
    except ImportError:
        print("  matplotlib not installed — skipping figure")


# ── print leaderboard to terminal ─────────────────────────────────────────────
def print_leaderboard(rows: list[dict]) -> None:
    print("\n" + "=" * 72)
    print("EvalBench OCR Leaderboard")
    print("=" * 72)
    header = f"{'Model':<18} {'Dataset':<12} {'N':>6}  {'CER':>6}  {'WER':>6}  {'EM':>6}  {'CharAcc':>8}  {'ms/img':>7}"
    print(header)
    print("-" * 72)
    for r in rows:
        print(f"{r['model']:<18} {r['dataset']:<12} {r['n_samples']:>6}  "
              f"{r['cer']:>6.3f}  {r['wer']:>6.3f}  {r['exact_match']:>6.3f}  "
              f"{r['char_accuracy']:>8.3f}  {r['latency_ms_avg']:>7.1f}")
    print("=" * 72)


# ── main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="EvalBench OCR evaluation")
    parser.add_argument("--models",   nargs="+",
                        default=["tesseract", "easyocr", "trocr_base"],
                        help="Models to evaluate")
    parser.add_argument("--datasets", nargs="+", default=None,
                        help="Datasets to include (default: all records with OCR GT)")
    parser.add_argument("--splits",   nargs="+", default=["test"],
                        help="Splits to use (default: test)")
    parser.add_argument("--append",   action="store_true",
                        help="Append to existing predictions.jsonl instead of overwriting")
    parser.add_argument("--n",        type=int, default=500,
                        help="Max samples per dataset (0 = full test set)")
    args = parser.parse_args()

    print(f"Loading records (splits={args.splits}) ...")
    records = load_test_records(args.datasets, splits=args.splits)
    print(f"  {len(records):,} test records with OCR ground truth")
    if not records:
        print("  No records found. Check that evalbench_v1.jsonl is built.")
        return

    # group by dataset for per-dataset sampling
    by_ds: dict[str, list] = defaultdict(list)
    for r in records:
        by_ds[r["dataset"]].append(r)
    for ds, recs in by_ds.items():
        n = args.n if args.n > 0 else len(recs)
        print(f"  {ds}: {len(recs):,} total → sampling {min(n, len(recs)):,}")

    all_results: list[dict] = []

    for model_name in args.models:
        print(f"\n{'─'*60}")
        print(f"Running: {model_name}")
        print(f"{'─'*60}")
        try:
            model = get_model(model_name)
        except ValueError as e:
            print(f"  {e}")
            continue

        model_records: list[dict] = []
        for ds, recs in by_ds.items():
            n_take = args.n if args.n > 0 else len(recs)
            model_records.extend(recs[:n_take])

        results = evaluate_model(model, model_records, n=0)  # already sampled above
        all_results.extend(results)
        print(f"  Done: {len(results)} predictions")

    if not all_results:
        print("No results generated.")
        return

    write_predictions(all_results, append=args.append)
    agg = aggregate(all_results)
    write_csv(agg)
    write_figure(agg)
    print_leaderboard(agg)


if __name__ == "__main__":
    main()
