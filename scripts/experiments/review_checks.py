#!/usr/bin/env python3
"""Checks added after reviewer-style feedback (Nov 2026). Run from the repository root:
  python3 scripts/experiments/review_checks.py > outputs/experiments/review_checks.txt
1. Track 1 sampling sensitivity: Tesseract 5 / EasyOCR / TrOCR-base on the common records (those PaddleOCR and OCR.space also
   processed) versus every record they processed (first 300 per corpus, reference >= 3 characters). Table 16 of Online Resource 1.
2. Track 5 evidence consistency: does the predicted total appear as a number in the EVIDENCE text, overall and for incorrect (> 3 marks) predictions.
3. SHA-256 prefixes of the grading and trust prompts (Table 17 of Online Resource 1).
"""
import json, re, hashlib, ast
import numpy as np
O = "outputs/experiments/"
rows = [json.loads(l) for l in open(O + "ocr/predictions.jsonl")]
osp = [json.loads(l) for l in open(O + "ocr/ocrspace_engine2_predictions.jsonl")]
ok = lambda r: len(r["ref"]) >= 3
print("== Track 1 sampling sensitivity (EM, CER)")
for ds in ("iam", "iiit_word"):
    common = {r["record_id"] for r in osp if r["dataset"] == ds}
    ids = sorted(r["record_id"] for r in rows if r["model"] == "tesseract5" and r["dataset"] == ds)
    print(f"{ds}: raw records {len(ids)}, first {ids[0]}, last {ids[-1]}, common n = {len(common)}")
    for m in ("tesseract5", "easyocr", "trocr_base"):
        rs = [r for r in rows if r["model"] == m and r["dataset"] == ds and ok(r)]
        cm = [r for r in rs if r["record_id"] in common]
        f = lambda x: f"n={len(x)} EM={np.mean([r['exact_match'] for r in x]):.3f} CER={np.mean([r['cer'] for r in x]):.3f}"
        print(f"  {m:11s} common {f(cm)} | all {f(rs)}")
print("== Track 5 evidence consistency (predicted total appears as a number in EVIDENCE)")
for d in ("fixed_model", "fixed_model_rep2"):
    rs = [json.loads(l) for l in open(O + f"{d}/track5_predictions.jsonl")]
    has = lambda r: any(abs(float(x) - r["pred_score"]) < 1e-9 for x in re.findall(r"\d+(?:\.\d+)?", r.get("evidence") or ""))
    wrong = [r for r in rs if abs(r["pred_score"] - r["true_score"]) > 3]
    print(f"{d}: all {sum(map(has, rs))}/{len(rs)}; incorrect {sum(map(has, wrong))}/{len(wrong)}")
print("== Prompt hashes (SHA-256, first 16 hex)")
for f, names in (("scripts/experiments/track3_assessment/run_assessment_eval.py", ["GRADING_PROMPT"]), ("scripts/experiments/track5_trust/run_trust_eval.py", ["TRUST_PROMPT"]),
                 ("scripts/experiments/annotation_leakage/run_masked.py", ["GRADING_PROMPT", "TRUST_PROMPT"])):
    for n in ast.parse(open(f).read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in names:
            print(f"{f.split('/')[-1]}: {n.targets[0].id} {hashlib.sha256(ast.literal_eval(n.value).encode()).hexdigest()[:16]}")
