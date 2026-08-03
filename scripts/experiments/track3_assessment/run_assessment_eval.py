"""
EvalBench — Track 3: Educational Assessment Evaluation
Evaluates VLMs on Mendeley exam grading task.

Task: Given a student exam paper (PDF → image), predict the total score.
Label: teacher_score (range 13–43, mean 27.9 in this dataset).
Note: No rubric is available — models grade holistically from the paper image.

Metrics: Score MAE, Pearson r, Spearman ρ, Exact Match (within ±1 mark)

Models (add API keys to env):
  - tesseract+llm: OCR text → LLM scoring (baseline)
  - florence2:     vision model (no API needed)
  - qwen2_5_vl:    open-source VLM
  - gpt4v:         GPT-4o via OpenAI API  (OPENAI_API_KEY)
  - gemini:        Gemini 1.5 Pro via API (GOOGLE_API_KEY)

Usage:
  python3 experiments/track3_assessment/run_assessment_eval.py
  python3 experiments/track3_assessment/run_assessment_eval.py --models florence2 gpt4v
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from collections import defaultdict

ROOT    = Path(__file__).parent.parent.parent
PROC    = ROOT / "datasets/processed"
OUT_DIR = ROOT / "outputs/experiments/track3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

GRADING_PROMPT = """\
You are an expert examiner reviewing a student examination paper.

Look carefully at the student's handwritten answers in this image.

Your task: Predict the TOTAL SCORE the teacher assigned to this paper.
The total score is the sum of marks for all questions.

Based on:
- Completeness: how many questions are answered
- Apparent correctness: whether answers look plausible and detailed
- Length and effort of written responses

Respond with ONLY a single integer or decimal number representing your predicted total score.
Do not explain. Do not add any text. Just the number.

Example response: 28
"""


# ── PDF → PIL Image ───────────────────────────────────────────────────────────

def pdf_to_image(pdf_path: Path, page: int = 0, dpi: int = 150):
    """Convert a PDF page to a PIL Image. Returns first page by default."""
    from PIL import Image
    try:
        import fitz  # PyMuPDF
        doc  = fitz.open(str(pdf_path))
        pg   = doc.load_page(page)
        mat  = fitz.Matrix(dpi / 72, dpi / 72)
        pix  = pg.get_pixmap(matrix=mat)
        img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except ImportError:
        pass
    try:
        from pdf2image import convert_from_path
        imgs = convert_from_path(str(pdf_path), dpi=dpi, first_page=page+1, last_page=page+1)
        return imgs[0] if imgs else None
    except ImportError:
        raise RuntimeError("Install PyMuPDF (pip3 install pymupdf) or pdf2image")


def parse_score(text: str) -> float | None:
    """Extract a number from model output."""
    text = text.strip()
    # direct number
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))
    return None


# ── load Mendeley records ──────────────────────────────────────────────────────

def load_mendeley() -> list[dict]:
    records = []
    with open(PROC / "evalbench_v1.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line.strip())
            if r["dataset"] == "mendeley" and r.get("teacher_score") is not None:
                records.append(r)
    return records


# ── model runners ─────────────────────────────────────────────────────────────

def run_florence2(records: list[dict]) -> list[dict]:
    import torch
    from transformers import AutoProcessor, AutoModelForCausalLM

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "microsoft/Florence-2-base"
    print(f"  Loading Florence-2-base on {device} ...")
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model     = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).to(device)
    model.eval()

    results = []
    for r in records:
        pdf_path = ROOT / r["image_path"]
        t0 = time.perf_counter()
        try:
            img  = pdf_to_image(pdf_path)
            task = "<MORE_DETAILED_CAPTION>"
            inp  = processor(text=task, images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                gen  = model.generate(input_ids=inp["input_ids"],
                                      pixel_values=inp["pixel_values"],
                                      max_new_tokens=512, num_beams=3)
            raw   = processor.batch_decode(gen, skip_special_tokens=False)[0]
            parsed = processor.post_process_generation(raw, task=task,
                                                        image_size=(img.width, img.height))
            desc  = parsed.get(task, "")
            # Florence-2 can't directly predict scores — use caption length as proxy score
            # For the paper this is a "baseline" — text model sees description
            pred_score = None  # Florence-2 generates captions, not scores
            raw_out    = desc[:200]
        except Exception as e:
            pred_score = None
            raw_out    = str(e)
        latency = (time.perf_counter() - t0) * 1000
        results.append({
            "model": "florence2", "record_id": r["record_id"],
            "true_score": r["teacher_score"], "pred_score": pred_score,
            "raw_output": raw_out, "latency_ms": round(latency, 1),
        })

    del model, processor
    if device == "mps":
        torch.mps.empty_cache()
    return results


def run_gpt4v(records: list[dict]) -> list[dict]:
    import openai, base64, io
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    results = []
    for r in records:
        pdf_path = ROOT / r["image_path"]
        t0 = time.perf_counter()
        try:
            img = pdf_to_image(pdf_path)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            b64 = base64.b64encode(buf.getvalue()).decode()
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text",       "text": GRADING_PROMPT},
                        {"type": "image_url",  "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }],
                max_tokens=20,
                temperature=0,
            )
            raw_out    = resp.choices[0].message.content.strip()
            pred_score = parse_score(raw_out)
        except Exception as e:
            raw_out    = str(e)
            pred_score = None
        latency = (time.perf_counter() - t0) * 1000
        results.append({
            "model": "gpt4o", "record_id": r["record_id"],
            "true_score": r["teacher_score"], "pred_score": pred_score,
            "raw_output": raw_out, "latency_ms": round(latency, 1),
        })
        time.sleep(0.5)   # rate limit
    return results


def run_gemini(records: list[dict]) -> list[dict]:
    import warnings; warnings.filterwarnings("ignore")
    from google import genai as gai
    from google.genai import types as gtypes
    import io
    client = gai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    model_id = "models/gemini-3.5-flash"
    results = []
    for idx, r in enumerate(records):
        pdf_path = ROOT / r["image_path"]
        t0 = time.perf_counter()
        raw_out, pred_score = "", None
        for attempt in range(4):
            try:
                img = pdf_to_image(pdf_path)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                resp = client.models.generate_content(
                    model=model_id,
                    contents=[
                        gtypes.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                        GRADING_PROMPT,
                    ],
                )
                raw_out    = resp.text.strip()
                pred_score = parse_score(raw_out)
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    wait = 30 * (attempt + 1)
                    print(f"  [{idx+1}/50] rate limit, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raw_out = msg
                    break
        latency = (time.perf_counter() - t0) * 1000
        results.append({
            "model": "gemini_3_5_flash", "record_id": r["record_id"],
            "true_score": r["teacher_score"], "pred_score": pred_score,
            "raw_output": raw_out, "latency_ms": round(latency, 1),
        })
        if pred_score is not None:
            print(f"  [{idx+1}/50] true={r['teacher_score']} pred={pred_score}")
        time.sleep(5.0)
    return results


def run_qwen_vl(records: list[dict]) -> list[dict]:
    import torch, io
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
    try:
        from qwen_vl_utils import process_vision_info
    except ImportError:
        raise RuntimeError("pip3 install qwen-vl-utils")

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"  Loading Qwen2.5-VL on {device} ...")
    model_id  = "Qwen/Qwen2.5-VL-7B-Instruct"
    processor = AutoProcessor.from_pretrained(model_id)
    model     = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_id, torch_dtype="auto").to(device)
    model.eval()

    results = []
    for r in records:
        pdf_path = ROOT / r["image_path"]
        t0 = time.perf_counter()
        try:
            img = pdf_to_image(pdf_path)
            messages = [{"role": "user", "content": [
                {"type": "image", "image": img},
                {"type": "text",  "text": GRADING_PROMPT},
            ]}]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                               padding=True, return_tensors="pt").to(device)
            with torch.no_grad():
                gen_ids = model.generate(**inputs, max_new_tokens=20)
            trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, gen_ids)]
            raw_out    = processor.batch_decode(trimmed, skip_special_tokens=True)[0].strip()
            pred_score = parse_score(raw_out)
        except Exception as e:
            raw_out    = str(e)
            pred_score = None
        latency = (time.perf_counter() - t0) * 1000
        results.append({
            "model": "qwen2_5_vl", "record_id": r["record_id"],
            "true_score": r["teacher_score"], "pred_score": pred_score,
            "raw_output": raw_out, "latency_ms": round(latency, 1),
        })

    del model, processor
    return results


MODEL_RUNNERS = {
    "florence2": run_florence2,
    "gpt4v":     run_gpt4v,
    "gemini":    run_gemini,
    "qwen_vl":   run_qwen_vl,
}


# ── metrics ───────────────────────────────────────────────────────────────────

def aggregate_metrics(results: list[dict]) -> dict:
    scored = [(r["true_score"], r["pred_score"])
              for r in results if r["pred_score"] is not None]
    if not scored:
        return {"n": len(results), "n_scored": 0}
    trues = [s[0] for s in scored]
    preds = [s[1] for s in scored]
    n     = len(scored)

    mae  = sum(abs(t - p) for t, p in zip(trues, preds)) / n
    em1  = sum(1 for t, p in zip(trues, preds) if abs(t - p) <= 1) / n

    # Pearson
    def pearson(x, y):
        mx, my = sum(x)/len(x), sum(y)/len(y)
        num    = sum((xi - mx)*(yi - my) for xi, yi in zip(x, y))
        dx     = (sum((xi - mx)**2 for xi in x) ** 0.5)
        dy     = (sum((yi - my)**2 for yi in y) ** 0.5)
        return num / (dx * dy) if dx * dy > 0 else 0.0

    # Spearman — rank then pearson
    def rank(lst):
        sorted_lst = sorted(enumerate(lst), key=lambda x: x[1])
        ranks = [0.0] * len(lst)
        for rank_val, (orig_idx, _) in enumerate(sorted_lst, 1):
            ranks[orig_idx] = float(rank_val)
        return ranks

    r_pearson  = pearson(trues, preds)
    r_spearman = pearson(rank(trues), rank(preds))

    return {
        "n":           len(results),
        "n_scored":    n,
        "mae":         round(mae, 3),
        "pearson_r":   round(r_pearson, 3),
        "spearman_r":  round(r_spearman, 3),
        "exact_pm1":   round(em1, 3),
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+",
                        default=["gpt4v", "gemini"],
                        help="Models to run (florence2, gpt4v, gemini, qwen_vl)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip records already successfully scored in predictions file")
    args = parser.parse_args()

    records = load_mendeley()
    print(f"Mendeley: {len(records)} records (score range "
          f"{min(r['teacher_score'] for r in records):.0f}–"
          f"{max(r['teacher_score'] for r in records):.0f})")

    pred_out = OUT_DIR / "track3_predictions.jsonl"

    # load existing successful results if resuming
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
            print(f"Unknown model: {model_name}. Available: {list(MODEL_RUNNERS)}")
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
            m = aggregate_metrics(results)
            print(f"  n={m['n']} scored={m['n_scored']} MAE={m.get('mae','?')} "
                  f"Pearson={m.get('pearson_r','?')} Spearman={m.get('spearman_r','?')}")
        except Exception as e:
            print(f"  Failed: {e}")

    if not all_results:
        print("\nNo results. Set OPENAI_API_KEY or GOOGLE_API_KEY and retry.")
        return

    with open(pred_out, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nWritten: {pred_out}")

    # write aggregate table
    by_model: dict[str, list] = defaultdict(list)
    for r in all_results:
        by_model[r["model"]].append(r)

    agg_rows = [{"model": m, **aggregate_metrics(rs)} for m, rs in by_model.items()]
    agg_out  = OUT_DIR / "track3_results.csv"
    if agg_rows:
        with open(agg_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=agg_rows[0].keys())
            writer.writeheader()
            writer.writerows(agg_rows)
        print(f"Written: {agg_out}")

    # print leaderboard
    print("\n" + "=" * 62)
    print("Track 3 — Educational Assessment Leaderboard (Mendeley)")
    print("=" * 62)
    print(f"{'Model':<20} {'N':>4} {'Scored':>6} {'MAE↓':>6} {'Pearson↑':>9} {'Spearman↑':>10} {'EM±1↑':>7}")
    print("-" * 62)
    for row in agg_rows:
        print(f"{row['model']:<20} {row['n']:>4} {row['n_scored']:>6} "
              f"{row.get('mae','—'):>6} {row.get('pearson_r','—'):>9} "
              f"{row.get('spearman_r','—'):>10} {row.get('exact_pm1','—'):>7}")
    print("=" * 62)


if __name__ == "__main__":
    main()
