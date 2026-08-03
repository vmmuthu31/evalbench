"""
EvalBench Paper 2 — Dataset Status Checker (English-only)
Run this any time to see what's downloaded vs. pending.
Usage: python3 dataset_status.py
"""

import os
from pathlib import Path

BASE = Path(__file__).parent.parent / "data_sources"

DATASETS = {
    "Tier 1 — Exam Grading (English)": {
        "anshcode1/AnswerScripts (HuggingFace)": {
            "path": BASE / "tier1_exam_grading/anshcode1_AnswerScripts",
            "source": "huggingface: anshcode1/AnswerScripts",
            "size": "~5,914 images",
        },
        "gopika13/answer_scripts (HuggingFace)": {
            "path": BASE / "tier1_exam_grading/gopika13_answer_scripts",
            "source": "huggingface: gopika13/answer_scripts",
            "size": "unknown",
        },
        "JunaidMB GCSE": {
            "path": BASE / "tier1_exam_grading/JunaidMB_GCSE",
            "source": "private — contact HuggingFace: JunaidMB (manual)",
            "size": "~78 samples",
            "manual": True,
        },
        "Mendeley sf3kvjwknt": {
            "path": BASE / "tier1_exam_grading/mendeley_sf3kvjwknt",
            "source": "https://data.mendeley.com/datasets/sf3kvjwknt/1",
            "size": "~50 scripts + marks",
        },
        "IEEE Answer Sheet Dataset": {
            "path": BASE / "tier1_exam_grading/IEEE_AnswerSheet",
            "source": "https://ieee-dataport.org (manual)",
            "size": "varies",
            "manual": True,
        },
    },
    "Tier 2 — English Handwriting Pretraining": {
        "IIIT English OCR (Training-Set)": {
            "path": BASE / "tier2_handwriting_pretrain/IIIT_English/Training-Set",
            "source": "https://ilocr.iiit.ac.in (manual)",
            "size": "varies",
            "manual": True,
        },
        "IIIT English OCR (Word-Level)": {
            "path": BASE / "tier2_handwriting_pretrain/IIIT_English/Word_Level",
            "source": "https://ilocr.iiit.ac.in (manual)",
            "size": "varies",
            "manual": True,
        },
        "IIIT English OCR (Page-Level)": {
            "path": BASE / "tier2_handwriting_pretrain/IIIT_English/Page_Level",
            "source": "https://ilocr.iiit.ac.in (manual)",
            "size": "varies",
            "manual": True,
        },
        "IAM Handwriting Database": {
            "path": BASE / "tier2_handwriting_pretrain/IAM_Handwriting",
            "source": "https://fki.tic.heia-fr.ch (registration)",
            "size": "~1,500 pages / 13K lines",
        },
    },
}


def folder_size(path: Path) -> str:
    if not path.exists():
        return "—"
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    for unit in ["B", "KB", "MB", "GB"]:
        if total < 1024:
            return f"{total:.1f} {unit}"
        total /= 1024
    return f"{total:.1f} TB"


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for f in path.rglob("*") if f.is_file())


GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def status_icon(path: Path, manual: bool = False) -> str:
    if not path.exists() or file_count(path) == 0:
        return f"{RED}✗ Missing{RESET}"
    if manual:
        return f"{YELLOW}⚠ Partial (manual step needed){RESET}"
    return f"{GREEN}✓ Downloaded{RESET}"


print(f"\n{BOLD}EvalBench Paper 2 — Dataset Status (English only){RESET}")
print("=" * 60)

total_ok = 0
total_miss = 0

for tier, datasets in DATASETS.items():
    print(f"\n{BOLD}{tier}{RESET}")
    print("-" * 60)
    for name, info in datasets.items():
        path = info["path"]
        manual = info.get("manual", False)
        icon = status_icon(path, manual)
        count = file_count(path)
        size = folder_size(path)
        print(f"  {name}")
        print(f"    Status : {icon}")
        print(f"    Files  : {count}   Size: {size}")
        print(f"    Expected: {info['size']}")
        print(f"    Source : {info['source']}")
        print()
        if "Missing" in icon:
            total_miss += 1
        else:
            total_ok += 1

print("=" * 60)
print(f"{BOLD}Summary:{RESET} {GREEN}{total_ok} ready{RESET}  |  {RED}{total_miss} missing/pending{RESET}")
print(f"\nRun {BOLD}./download_datasets.sh{RESET} to fetch missing datasets.")
print(f"Datasets with ⚠ need manual download from the listed source.\n")
