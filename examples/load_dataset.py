"""
Minimal example: load the EvalBench v1 processed manifest and filter by track/split.

Usage:
    python3 examples/load_dataset.py --track ocr_substrate --split test
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / "data" / "processed" / "evalbench_v1.jsonl"


def load(track: str | None = None, split: str | None = None) -> list[dict]:
    records = []
    with open(MANIFEST, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if track and r.get("track") != track:
                continue
            if split and r.get("split") != split:
                continue
            records.append(r)
    return records


def main():
    parser = argparse.ArgumentParser(description="Load EvalBench v1 records")
    parser.add_argument("--track", default=None, help="e.g. ocr_substrate, scored_answer_core, multimodal")
    parser.add_argument("--split", default=None, help="train, val, or test")
    args = parser.parse_args()

    records = load(track=args.track, split=args.split)
    print(f"Loaded {len(records):,} records (track={args.track}, split={args.split})")

    by_dataset = Counter(r["dataset"] for r in records)
    for dataset, n in sorted(by_dataset.items(), key=lambda x: -x[1]):
        print(f"  {dataset:<15} {n:>7,}")

    if records:
        print("\nExample record:")
        print(json.dumps(records[0], indent=2)[:600])


if __name__ == "__main__":
    main()
