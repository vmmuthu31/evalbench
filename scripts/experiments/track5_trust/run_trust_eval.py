"""
EvalBench — Track 5: Trustworthiness Evaluation
Measures confidence calibration, grounding, and explanation quality.

Task: Given an exam paper + predicted score, ask the model to:
  1. Assign a score (0–max)
  2. State confidence (0.0–1.0)
  3. Provide evidence (quote from paper)
  4. Explain the reasoning

Metrics:
  - ECE (Expected Calibration Error) — calibration of stated confidence vs accuracy
  - AUROC — discrimination: can confidence distinguish right from wrong predictions
  - Grounding rate — % of predictions that cite specific evidence
  - Explanation faithfulness — human eval placeholder (auto: length + structure heuristic)

This is operationalised on Mendeley (50 graded exam papers with teacher scores).
A prediction is "correct" if |pred_score - teacher_score| ≤ tolerance (default 3 marks).

Usage:
  python3 experiments/track5_trust/run_trust_eval.py --models gpt4v gemini
  # API keys: OPENAI_API_KEY, GOOGLE_API_KEY
"""

from __future__ import annotations
import argparse
import csv
import json
import math
import os
import re
import time
from collections import defaultdict
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
PROC    = ROOT / "datasets/processed"
OUT_DIR = ROOT / "outputs/experiments/track5"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRUST_PROMPT = """\
You are an AI examiner evaluating a student's handwritten exam paper.

TASK:
1. Estimate the total score for this paper (a number from 0 to 50).
2. State your confidence in this score from 0.0 (not confident) to 1.0 (very confident).
3. Quote specific evidence from the paper that informed your score estimate.
4. Briefly explain your reasoning (1-3 sentences).

Respond in this EXACT format — nothing else:
SCORE: <number>
CONFIDENCE: <decimal 0.0-1.0>
EVIDENCE: <direct quote or observation from the paper>
REASONING: <1-3 sentence explanation>
"""


# ── PDF → PIL Image ───────────────────────────────────────────────────────────

def pdf_to_image(pdf_path: Path, dpi: int = 150):
    from PIL import Image
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        pg  = doc.load_page(0)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = pg.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except ImportError:
        from pdf2image import convert_from_path
        imgs = convert_from_path(str(pdf_path), dpi=dpi, first_page=1, last_page=1)
        return imgs[0]


def parse_trust_response(text: str) -> dict:
    """Parse SCORE / CONFIDENCE / EVIDENCE / REASONING from model output."""
    result = {"pred_score": None, "confidence": None, "evidence": None, "reasoning": None}
    lines  = text.strip().splitlines()
    for line in lines:
        if line.upper().startswith("SCORE:"):
            m = re.search(r"(\d+(?:\.\d+)?)", line)
            if m:
                result["pred_score"] = float(m.group(1))
        elif line.upper().startswith("CONFIDENCE:"):
            m = re.search(r"(\d+(?:\.\d+)?)", line)
            if m:
                result["confidence"] = min(1.0, max(0.0, float(m.group(1))))
        elif line.upper().startswith("EVIDENCE:"):
            result["evidence"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("REASONING:"):
            result["reasoning"] = line.split(":", 1)[1].strip()
    return result


# ── model runners ─────────────────────────────────────────────────────────────

def run_gpt4v(records: list[dict]) -> list[dict]:
    import openai, base64, io
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    results = []
    for r in records:
        t0 = time.perf_counter()
        try:
            img = pdf_to_image(ROOT / r["image_path"])
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            b64 = base64.b64encode(buf.getvalue()).decode()
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "text",      "text": TRUST_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ]}],
                max_tokens=256, temperature=0,
            )
            raw     = resp.choices[0].message.content
            parsed  = parse_trust_response(raw)
        except Exception as e:
            raw, parsed = str(e), {}
        latency = (time.perf_counter() - t0) * 1000
        results.append({
            "model":       "gpt4o",
            "record_id":   r["record_id"],
            "true_score":  r["teacher_score"],
            "raw_output":  raw,
            "latency_ms":  round(latency, 1),
            **{k: parsed.get(k) for k in ("pred_score", "confidence", "evidence", "reasoning")},
        })
        time.sleep(0.5)
    return results


def run_gemini(records: list[dict]) -> list[dict]:
    import warnings; warnings.filterwarnings("ignore")
    from google import genai as gai
    from google.genai import types as gtypes
    import io
    client = gai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    model_id = "models/gemini-3.1-flash-lite"
    results = []
    for idx, r in enumerate(records):
        t0 = time.perf_counter()
        raw, parsed = "", {}
        for attempt in range(4):
            try:
                img = pdf_to_image(ROOT / r["image_path"])
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                resp = client.models.generate_content(
                    model=model_id,
                    contents=[
                        gtypes.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                        TRUST_PROMPT,
                    ],
                )
                raw    = resp.text.strip()
                parsed = parse_trust_response(raw)
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    wait = 30 * (attempt + 1)
                    print(f"  [{idx+1}/50] rate limit, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raw = msg
                    break
        latency = (time.perf_counter() - t0) * 1000
        results.append({
            "model":       "gemini_3_1_flash_lite",
            "record_id":   r["record_id"],
            "true_score":  r["teacher_score"],
            "raw_output":  raw,
            "latency_ms":  round(latency, 1),
            **{k: parsed.get(k) for k in ("pred_score", "confidence", "evidence", "reasoning")},
        })
        if parsed.get("pred_score") is not None:
            print(f"  [{idx+1}/50] score={parsed['pred_score']} conf={parsed.get('confidence','?')}")
        time.sleep(5.0)
    return results


MODEL_RUNNERS = {"gpt4v": run_gpt4v, "gemini": run_gemini}


# ── trustworthiness metrics ────────────────────────────────────────────────────

def compute_trust_metrics(results: list[dict], correct_tol: float = 3.0,
                           n_bins: int = 10) -> dict:
    """
    ECE: bucket predictions by confidence, compare bucket accuracy vs mean confidence.
    AUROC: AUC of ROC curve where label=correct (|pred-true|<=tol), score=confidence.
    Grounding rate: fraction with non-empty evidence field.
    """
    scored = [r for r in results if r.get("pred_score") is not None
              and r.get("confidence") is not None]
    if not scored:
        return {"n": len(results), "n_scored": 0}

    true_scores = [r["true_score"]  for r in scored]
    pred_scores = [r["pred_score"]  for r in scored]
    confs       = [r["confidence"]  for r in scored]
    corrects    = [int(abs(t - p) <= correct_tol) for t, p in zip(true_scores, pred_scores)]

    # ECE
    bins     = [[] for _ in range(n_bins)]
    for conf, correct in zip(confs, corrects):
        b = min(int(conf * n_bins), n_bins - 1)
        bins[b].append((conf, correct))
    ece = 0.0
    for b in bins:
        if not b:
            continue
        avg_conf = sum(x[0] for x in b) / len(b)
        avg_acc  = sum(x[1] for x in b) / len(b)
        ece     += abs(avg_conf - avg_acc) * len(b) / len(scored)

    # AUROC (trapezoidal)
    paired = list(zip(confs, corrects))
    paired.sort(key=lambda x: -x[0])
    n_pos  = sum(corrects)
    n_neg  = len(corrects) - n_pos
    if n_pos == 0 or n_neg == 0:
        auroc = 0.5
    else:
        tp, fp, prev_tp, prev_fp = 0, 0, 0, 0
        auroc = 0.0
        for conf, correct in paired:
            if correct:
                tp += 1
            else:
                fp += 1
            auroc += (fp - prev_fp) / n_neg * (tp + prev_tp) / (2 * n_pos)
            prev_tp, prev_fp = tp, fp

    grounding_rate = sum(1 for r in results if r.get("evidence") and len(r["evidence"]) > 5) / len(results)
    has_reasoning  = sum(1 for r in results if r.get("reasoning") and len(r["reasoning"]) > 10) / len(results)

    mae = sum(abs(t - p) for t, p in zip(true_scores, pred_scores)) / len(scored)

    return {
        "n":               len(results),
        "n_scored":        len(scored),
        "mae":             round(mae, 3),
        "accuracy_pm3":    round(sum(corrects) / len(scored), 3),
        "ece":             round(ece, 4),
        "auroc":           round(auroc, 4),
        "grounding_rate":  round(grounding_rate, 3),
        "reasoning_rate":  round(has_reasoning, 3),
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["gpt4v", "gemini"])
    parser.add_argument("--tol",    type=float, default=3.0)
    parser.add_argument("--resume", action="store_true",
                        help="Skip records already successfully scored")
    args = parser.parse_args()

    records = []
    with open(PROC / "evalbench_v1.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line.strip())
            if r["dataset"] == "mendeley" and r.get("teacher_score") is not None:
                records.append(r)
    print(f"Mendeley: {len(records)} records")

    pred_out = OUT_DIR / "track5_predictions.jsonl"
    existing: list[dict] = []
    done_ids: set = set()
    if args.resume and pred_out.exists():
        with open(pred_out, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r.get("pred_score") is not None:
                    existing.append(r)
                    done_ids.add(r["record_id"])
        print(f"  Resuming: {len(done_ids)} already scored, {len(records)-len(done_ids)} remaining")

    all_results: list[dict] = list(existing)

    for model_name in args.models:
        if model_name not in MODEL_RUNNERS:
            print(f"Unknown: {model_name}")
            continue
        if model_name == "gpt4v" and not os.environ.get("OPENAI_API_KEY"):
            print(f"  Skipping {model_name}: OPENAI_API_KEY not set")
            continue
        if model_name == "gemini" and not os.environ.get("GOOGLE_API_KEY"):
            print(f"  Skipping {model_name}: GOOGLE_API_KEY not set")
            continue

        to_run = [r for r in records if r["record_id"] not in done_ids] if args.resume else records
        if not to_run:
            print(f"  {model_name}: all records already scored")
            continue

        print(f"\n{'─'*50}\nRunning: {model_name} ({len(to_run)} records)\n{'─'*50}")
        try:
            results = MODEL_RUNNERS[model_name](to_run)
            all_results.extend(results)
            m = compute_trust_metrics(results, args.tol)
            print(f"  ECE={m.get('ece','?')} AUROC={m.get('auroc','?')} "
                  f"Grounding={m.get('grounding_rate','?')} MAE={m.get('mae','?')}")
        except Exception as e:
            print(f"  Failed: {e}")
            import traceback; traceback.print_exc()

    if not all_results:
        print("\nNo results. Set OPENAI_API_KEY or GOOGLE_API_KEY and retry.")
        return

    with open(pred_out, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Written: {pred_out}")

    by_model: dict[str, list] = defaultdict(list)
    for r in all_results:
        by_model[r["model"]].append(r)

    agg_rows = [{"model": m, **compute_trust_metrics(rs, args.tol)}
                for m, rs in by_model.items()]
    agg_out = OUT_DIR / "track5_results.csv"
    if agg_rows:
        with open(agg_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=agg_rows[0].keys())
            writer.writeheader()
            writer.writerows(agg_rows)
        print(f"Written: {agg_out}")

    print("\n" + "=" * 74)
    print("Track 5 — Trustworthiness Leaderboard (Mendeley, tol=±{})".format(args.tol))
    print("=" * 74)
    print(f"{'Model':<22}  {'ECE↓':>5}  {'AUROC↑':>7}  {'Ground↑':>8}  {'Reason↑':>8}  {'MAE↓':>5}")
    print("-" * 74)
    for row in agg_rows:
        print(f"{row['model']:<22}  {row.get('ece','—'):>5}  {row.get('auroc','—'):>7}  "
              f"{row.get('grounding_rate','—'):>8}  {row.get('reasoning_rate','—'):>8}  "
              f"{row.get('mae','—'):>5}")
    print("=" * 74)


if __name__ == "__main__":
    main()
