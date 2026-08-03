"""
EvalBench — Phase 5: Publication-ready statistics
Generates:
  - outputs/tables/table1_dataset_comparison.csv   (Table 1 of paper)
  - outputs/tables/dataset_statistics.csv          (full stats)
  - outputs/figures/split_distribution.png
  - outputs/figures/track_distribution.png
  - outputs/figures/records_per_dataset.png

Usage: python3 scripts/generate_statistics.py
"""

import json
from pathlib import Path
from collections import Counter
from PIL import Image
import statistics

ROOT     = Path(__file__).parent.parent
PROC     = ROOT / "datasets/processed"
TABLES   = ROOT / "outputs/tables"
FIGURES  = ROOT / "outputs/figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

# ── load evalbench ─────────────────────────────────────────────────────────────
print("Loading evalbench_v1.jsonl ...")
records = []
with open(PROC / "evalbench_v1.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))
print(f"  {len(records):,} records loaded")

# ── per-dataset stats ──────────────────────────────────────────────────────────
TRACK_MAP = {
    "mendeley":  "Track 3 + 5",
    "iam":       "Track 1 + 2",
    "iiit_word": "Track 1",
    "iiit_page": "Track 1 + 2",
    "anshcode1": "Track 1",
    "gopika13":  "Track 1 + 4",
    "ieee":      "Track 2 + 3",
}

DATASET_META = {
    "mendeley":  {"license": "CC BY 4.0", "language": "English", "has_score": True,  "has_ocr": False},
    "iam":       {"license": "CC BY 4.0", "language": "English", "has_score": False, "has_ocr": True},
    "iiit_word": {"license": "CC BY 4.0", "language": "English", "has_score": False, "has_ocr": True},
    "iiit_page": {"license": "CC BY 4.0", "language": "English", "has_score": False, "has_ocr": True},
    "anshcode1": {"license": "CC BY 4.0", "language": "English", "has_score": False, "has_ocr": False},
    "gopika13":  {"license": "CC BY 4.0", "language": "English", "has_score": False, "has_ocr": True},
    "ieee":      {"license": "CC BY 4.0", "language": "English", "has_score": True,  "has_ocr": True},
}

by_dataset = {}
for r in records:
    ds = r["dataset"]
    if ds not in by_dataset:
        by_dataset[ds] = {"records": 0, "with_image": 0, "with_ocr": 0, "with_score": 0,
                          "splits": Counter(), "widths": [], "heights": []}
    by_dataset[ds]["records"]    += 1
    by_dataset[ds]["with_image"] += 1 if r.get("image_path") else 0
    by_dataset[ds]["with_ocr"]   += 1 if r.get("ocr_text")   else 0
    by_dataset[ds]["with_score"] += 1 if r.get("teacher_score") is not None else 0
    by_dataset[ds]["splits"][r["split"]] += 1

# ── sample image resolutions ───────────────────────────────────────────────────
print("Sampling image resolutions (up to 200 per dataset)...")
for ds, stats in by_dataset.items():
    recs_with_img = [r for r in records if r["dataset"] == ds and r.get("image_path")]
    sample = recs_with_img[:200]
    for r in sample:
        img_path = ROOT / r["image_path"]
        if img_path.exists():
            try:
                with Image.open(img_path) as img:
                    w, h = img.size
                    stats["widths"].append(w)
                    stats["heights"].append(h)
            except Exception:
                pass

# ── write dataset_statistics.csv ──────────────────────────────────────────────
import csv
stats_file = TABLES / "dataset_statistics.csv"
with open(stats_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["dataset", "records", "with_image", "with_ocr", "with_teacher_score",
                     "train", "val", "test", "avg_width", "avg_height",
                     "license", "language", "tracks"])
    for ds, s in sorted(by_dataset.items(), key=lambda x: -x[1]["records"]):
        meta = DATASET_META.get(ds, {})
        avg_w = round(statistics.mean(s["widths"]),  1) if s["widths"]  else ""
        avg_h = round(statistics.mean(s["heights"]), 1) if s["heights"] else ""
        writer.writerow([
            ds, s["records"], s["with_image"], s["with_ocr"], s["with_score"],
            s["splits"].get("train", 0), s["splits"].get("val", 0), s["splits"].get("test", 0),
            avg_w, avg_h,
            meta.get("license", "CC BY 4.0"),
            meta.get("language", "English"),
            TRACK_MAP.get(ds, ""),
        ])
print(f"  Written: {stats_file}")

# ── write Table 1 (paper-ready comparison) ────────────────────────────────────
table1_file = TABLES / "table1_dataset_comparison.csv"
with open(table1_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Dataset", "Records", "Has Images", "Has OCR",
                     "Teacher Scores", "License", "Track(s)"])
    for ds, s in sorted(by_dataset.items(), key=lambda x: -x[1]["records"]):
        meta  = DATASET_META.get(ds, {})
        name  = {"mendeley": "Mendeley sf3kvjwknt", "iam": "IAM Handwriting",
                 "iiit_word": "IIIT English Word", "iiit_page": "IIIT English Page",
                 "anshcode1": "anshcode1 AnswerScripts", "gopika13": "gopika13 Answer Scripts",
                 "ieee": "IEEE Answer Sheet"}.get(ds, ds)
        writer.writerow([
            name,
            f"{s['records']:,}",
            "✓" if s["with_image"] > 0  else "✗",
            "✓" if s["with_ocr"]   > 0  else "✗",
            "✓" if s["with_score"] > 0  else "✗",
            meta.get("license", "CC BY 4.0"),
            TRACK_MAP.get(ds, ""),
        ])
    # totals row
    total_r = sum(s["records"]    for s in by_dataset.values())
    total_i = sum(s["with_image"] for s in by_dataset.values())
    total_o = sum(s["with_ocr"]   for s in by_dataset.values())
    total_s = sum(s["with_score"] for s in by_dataset.values())
    writer.writerow(["TOTAL", f"{total_r:,}", f"{total_i:,}", f"{total_o:,}", f"{total_s:,}", "", ""])
print(f"  Written: {table1_file}")

# ── figures ────────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    COLORS = ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B2","#937860","#DA8BC3"]

    # Figure 1 — Records per dataset (horizontal bar)
    fig, ax = plt.subplots(figsize=(9, 5))
    ds_names  = [{"mendeley":"Mendeley","iam":"IAM","iiit_word":"IIIT Word",
                  "iiit_page":"IIIT Page","anshcode1":"anshcode1","gopika13":"gopika13",
                  "ieee":"IEEE"}.get(d, d) for d in by_dataset]
    ds_counts = [s["records"] for s in by_dataset.values()]
    bars = ax.barh(ds_names, ds_counts, color=COLORS[:len(ds_names)])
    for bar, count in zip(bars, ds_counts):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                f"{count:,}", va="center", fontsize=9)
    ax.set_xlabel("Number of Records")
    ax.set_title("EvalBench v1 — Records per Dataset")
    ax.set_xlim(0, max(ds_counts) * 1.15)
    plt.tight_layout()
    fig.savefig(FIGURES / "records_per_dataset.png", dpi=150)
    plt.close()
    print(f"  Written: {FIGURES / 'records_per_dataset.png'}")

    # Figure 2 — Split distribution (stacked bar)
    splits   = ["train", "val", "test"]
    split_colors = ["#4C72B0", "#55A868", "#DD8452"]
    ds_list  = list(by_dataset.keys())
    ds_short = [{"mendeley":"Mendeley","iam":"IAM","iiit_word":"IIIT\nWord",
                 "iiit_page":"IIIT\nPage","anshcode1":"ansh\ncode1","gopika13":"gopika13",
                 "ieee":"IEEE"}.get(d, d) for d in ds_list]
    x        = np.arange(len(ds_list))
    bottoms  = np.zeros(len(ds_list))
    fig, ax  = plt.subplots(figsize=(10, 5))
    for split, color in zip(splits, split_colors):
        vals = [by_dataset[ds]["splits"].get(split, 0) for ds in ds_list]
        ax.bar(x, vals, bottom=bottoms, label=split.capitalize(), color=color)
        bottoms += np.array(vals)
    ax.set_xticks(x)
    ax.set_xticklabels(ds_short, fontsize=9)
    ax.set_ylabel("Records")
    ax.set_title("EvalBench v1 — Split Distribution by Dataset")
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIGURES / "split_distribution.png", dpi=150)
    plt.close()
    print(f"  Written: {FIGURES / 'split_distribution.png'}")

    # Figure 3 — Track distribution (pie)
    track_counts = Counter(TRACK_MAP.get(r["dataset"], "other") for r in records)
    fig, ax = plt.subplots(figsize=(7, 7))
    labels  = list(track_counts.keys())
    sizes   = list(track_counts.values())
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=COLORS[:len(labels)],
           startangle=140, textprops={"fontsize": 9})
    ax.set_title("EvalBench v1 — Records by Track Assignment")
    plt.tight_layout()
    fig.savefig(FIGURES / "track_distribution.png", dpi=150)
    plt.close()
    print(f"  Written: {FIGURES / 'track_distribution.png'}")

except ImportError:
    print("  matplotlib not installed — skipping figures. Run: pip3 install matplotlib")

# ── print summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("EvalBench v1 — Statistics Summary")
print("=" * 60)
for ds, s in sorted(by_dataset.items(), key=lambda x: -x[1]["records"]):
    avg_w = f"{round(statistics.mean(s['widths']),0):.0f}" if s["widths"] else "N/A"
    avg_h = f"{round(statistics.mean(s['heights']),0):.0f}" if s["heights"] else "N/A"
    print(f"\n  {ds}")
    print(f"    Records      : {s['records']:,}")
    print(f"    With image   : {s['with_image']:,}")
    print(f"    With OCR     : {s['with_ocr']:,}")
    print(f"    With score   : {s['with_score']:,}")
    print(f"    Splits       : train={s['splits'].get('train',0):,}  val={s['splits'].get('val',0):,}  test={s['splits'].get('test',0):,}")
    print(f"    Avg res      : {avg_w} x {avg_h} px")
    print(f"    Tracks       : {TRACK_MAP.get(ds, '')}")

print(f"\n  TOTAL RECORDS  : {total_r:,}")
print(f"  TOTAL W/ IMAGE : {total_i:,}")
print(f"  TOTAL W/ OCR   : {total_o:,}")
print(f"  TOTAL W/ SCORE : {total_s:,}")
print("=" * 60)
print("\nOutputs written to outputs/tables/ and outputs/figures/")
