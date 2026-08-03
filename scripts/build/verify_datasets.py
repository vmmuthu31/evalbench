"""
EvalBench — Dataset Verification Script
Reads metadata/datasets.yaml and reports actual vs expected file counts and sizes.
Usage: python3 scripts/verify_datasets.py
"""

import os
import yaml
from pathlib import Path

BASE      = Path(__file__).parent.parent
META_FILE = BASE / "metadata" / "datasets.yaml"

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for f in path.rglob("*") if f.is_file())


def folder_size_gb(path: Path) -> float:
    if not path.exists():
        return 0.0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / (1024 ** 3), 3)


def status(actual_files, expected_files):
    if actual_files == 0:
        return f"{RED}✗ Missing{RESET}"
    if expected_files and actual_files < expected_files * 0.8:
        return f"{YELLOW}⚠ Partial{RESET}"
    return f"{GREEN}✓ OK{RESET}"


with open(META_FILE) as f:
    meta = yaml.safe_load(f)

datasets = meta["datasets"]

print(f"\n{BOLD}EvalBench — Dataset Verification{RESET}")
print("=" * 65)

total_files = 0
total_size  = 0.0
all_ok      = True

for ds in datasets:
    name     = ds["name"]
    expected = ds.get("files")
    local    = BASE / ds["local_path"]
    actual   = file_count(local)
    size_gb  = folder_size_gb(local)
    st       = status(actual, expected)

    total_files += actual
    total_size  += size_gb

    if "Missing" in st or "Partial" in st:
        all_ok = False

    exp_str = f"{expected:,}" if expected else "unknown"
    print(f"\n  {BOLD}{name}{RESET}")
    print(f"    Status   : {st}")
    print(f"    Files    : {actual:,}  (expected: {exp_str})")
    print(f"    Size     : {size_gb:.3f} GB")
    print(f"    License  : {ds['license']}")
    print(f"    Tracks   : {', '.join(ds['tracks'])}")

print("\n" + "=" * 65)
print(f"{BOLD}Total files : {total_files:,}{RESET}")
print(f"{BOLD}Total size  : {total_size:.2f} GB{RESET}")

if all_ok:
    print(f"\n{GREEN}{BOLD}All datasets verified.{RESET}")
else:
    print(f"\n{YELLOW}{BOLD}Some datasets missing or partial — check above.{RESET}")
print()
