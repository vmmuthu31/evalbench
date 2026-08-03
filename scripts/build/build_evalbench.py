"""
EvalBench — Build evalbench_v1.parquet
Runs all extractors, merges into one parquet, prints publication-ready stats.
Usage: python3 scripts/build_evalbench.py
"""

import json, subprocess, sys
from pathlib import Path
from collections import Counter

ROOT     = Path(__file__).parent.parent
PROC_DIR = ROOT / "datasets/processed"
OUT_PQ   = ROOT / "datasets/processed/evalbench_v1.parquet"
OUT_JSONL= ROOT / "datasets/processed/evalbench_v1.jsonl"

EXTRACTORS = [
    "extract_mendeley.py",
    "extract_gopika13.py",
    "extract_iam.py",
    "extract_iiit_word.py",
    "extract_iiit_page.py",
    "extract_anshcode1.py",
]

JSONL_FILES = [
    "mendeley_records.jsonl",
    "gopika13_records.jsonl",
    "iam_records.jsonl",
    "iiit_word_records.jsonl",
    "iiit_page_records.jsonl",
    "anshcode1_records.jsonl",
    "ieee_records.jsonl",       # added after institutional download
]

GREEN = "\033[92m"; BOLD = "\033[1m"; RESET = "\033[0m"; RED = "\033[91m"

# ── Step 1: run extractors ────────────────────────────────────────────────────
print(f"\n{BOLD}Step 1 — Running extractors{RESET}")
print("=" * 60)
scripts_dir = ROOT / "scripts"
for extractor in EXTRACTORS:
    script = scripts_dir / extractor
    print(f"\n  Running {extractor}...")
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  {RED}FAILED{RESET}: {result.stderr[-500:]}")
    else:
        for line in result.stdout.strip().splitlines():
            print(f"    {line}")

# ── Step 2: merge all jsonl files ─────────────────────────────────────────────
print(f"\n{BOLD}Step 2 — Merging records{RESET}")
print("=" * 60)
all_records = []
for fname in JSONL_FILES:
    fpath = PROC_DIR / fname
    if not fpath.exists():
        print(f"  SKIP (not found): {fname}")
        continue
    before = len(all_records)
    with open(fpath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                all_records.append(json.loads(line))
    print(f"  {fname}: {len(all_records) - before:,} records")

print(f"\n  Total merged: {len(all_records):,} records")

# write merged jsonl
with open(OUT_JSONL, "w", encoding="utf-8") as f:
    for r in all_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"  Written: {OUT_JSONL}")

# write parquet
try:
    import pandas as pd
    df = pd.DataFrame(all_records)
    # extra column is a dict — keep as json string for parquet compatibility
    df["extra"] = df["extra"].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
    df.to_parquet(OUT_PQ, index=False)
    print(f"  Written: {OUT_PQ}")
except Exception as e:
    print(f"  Parquet write failed: {e} (jsonl still saved)")

# ── Step 3: statistics ────────────────────────────────────────────────────────
print(f"\n{BOLD}Step 3 — Benchmark Statistics{RESET}")
print("=" * 60)

by_dataset     = Counter(r["dataset"]       for r in all_records)
by_track       = Counter(r["track"]         for r in all_records)
by_split       = Counter(r["split"]         for r in all_records)
with_image     = sum(1 for r in all_records if r.get("image_path"))
with_ocr       = sum(1 for r in all_records if r.get("ocr_text"))
with_score     = sum(1 for r in all_records if r.get("teacher_score") is not None)

print(f"\n  {BOLD}By dataset:{RESET}")
for ds, n in sorted(by_dataset.items(), key=lambda x: -x[1]):
    print(f"    {ds:<30} {n:>8,}")

print(f"\n  {BOLD}By track:{RESET}")
for track, n in sorted(by_track.items(), key=lambda x: -x[1]):
    print(f"    {track:<30} {n:>8,}")

print(f"\n  {BOLD}By split:{RESET}")
for split, n in sorted(by_split.items()):
    print(f"    {split:<30} {n:>8,}")

print(f"\n  {BOLD}Coverage:{RESET}")
total = len(all_records)
print(f"    Total records      : {total:,}")
print(f"    With image         : {with_image:,}  ({100*with_image/total:.1f}%)")
print(f"    With OCR text      : {with_ocr:,}  ({100*with_ocr/total:.1f}%)")
print(f"    With teacher score : {with_score:,}  ({100*with_score/total:.1f}%)")

print(f"\n{GREEN}{BOLD}EvalBench v1 build complete.{RESET}\n")
