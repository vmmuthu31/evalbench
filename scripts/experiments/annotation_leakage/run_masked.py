"""Annotation-free replication of EvalBench Tracks 3 and 5, plus an independent-grading condition (Track 3b).
Model: gemini-3.5-flash, temperature 0, seed 42 (same as the fixed-model runs).
Conditions (all on the RAW student scans, Student_Pdf, which carry no teacher ink):
  e1t3  page 1 only, original Track 3 prompt          (same prompt as the annotated runs)
  e1t5  page 1 only, original Track 5 prompt
  e3b   all 4 pages + question paper + answer key/rubric, grade the paper (independent grading)
Usage: GEMINI_KEYS_FILE=keys.txt python3 run_masked.py <mode> <run_name> [seconds_budget]"""
import sys, os, io, csv, json, re, time, threading, glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import fitz
from PIL import Image
from google import genai as gai
from google.genai import types as gt

D = Path(os.environ.get("MENDELEY_DIR", "/tmp/mend/d/A Dataset of Digitized Student Examination Papers,"))
HERE = Path(__file__).parent
MODEL = "models/gemini-3.5-flash"
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
def grade_prompt():
    q = (D/"Question.txt").read_text(); k = (D/"answerkey.txt").read_text()
    return f"""You are an experienced examiner marking a Data Science examination. The student's handwritten answer pages are attached (4 pages, unmarked scans). 

QUESTION PAPER:
{q}

ANSWER KEY AND EXPECTED KEY POINTS (CSV: question number, type, correct answer / expected points):
{k}

MARKING SCHEME: Part I has 20 multiple-choice questions at 1 mark each (full mark only if the chosen option matches the key). Part II has 15 short-answer questions at 2 marks each; award 0 to 2 marks (halves allowed) according to how many of the expected key points the answer contains. The maximum total is 50. An unanswered question scores 0.

TASK: Mark the paper from the handwritten answers only. Respond in this EXACT format and nothing else:
MCQ_SCORE: <number out of 20>
SHORT_SCORE: <number out of 30>
TOTAL: <number out of 50>
CONFIDENCE: <decimal 0.0-1.0, your confidence that TOTAL is within 3 marks of the true total>
REASONING: <1-3 sentences>
"""
def render_masked(student, width=1240):
    import numpy as np
    from scipy.ndimage import binary_dilation
    doc = fitz.open(str(D/"Corrected_Pdf"/f"Student_{student}.pdf")); pg = doc.load_page(0); z = width / pg.rect.width
    pix = pg.get_pixmap(matrix=fitz.Matrix(z, z)); a = np.array(Image.frombytes("RGB", [pix.width, pix.height], pix.samples)).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; red = (r > 130) & (r - g > 60) & (r - b > 60)
    a[binary_dilation(red, iterations=3)] = 255; doc.close()
    return [Image.fromarray(a.astype("uint8"))]
def render(student, pages, width=1240):
    out = []
    doc = fitz.open(str(D/"Student_Pdf"/f"Student_{student}.pdf"))
    for p in [q for q in pages if q < len(doc)]:
        pg = doc.load_page(p); z = width / pg.rect.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(z, z)); im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        out.append(im)
    doc.close(); return out
KEYS = [k.strip() for k in open(os.environ["GEMINI_KEYS_FILE"]) if k.strip()]
_kl = threading.Lock()
_DF = HERE / (".dead_" + time.strftime("%Y%m%d", time.gmtime()))
_dead = set(int(x) for x in _DF.read_text().split()) if _DF.exists() else set()
_rr = [0]
def _key():
    with _kl:
        n = len(KEYS)
        for _ in range(n):
            i = _rr[0] % n; _rr[0] += 1
            if i not in _dead: return i
    return None
cfg = gt.GenerateContentConfig(temperature=0.0, seed=42)
def call(images, prompt):
    parts = []
    for im in images:
        b = io.BytesIO(); im.save(b, format="PNG"); parts.append(gt.Part.from_bytes(data=b.getvalue(), mime_type="image/png"))
    for attempt in range(40):
        i = _key()
        if i is None: return "ERROR: all keys exhausted"
        try:
            c = gai.Client(api_key=KEYS[i])
            return c.models.generate_content(model=MODEL, contents=parts + [prompt], config=cfg).text.strip()
        except Exception as e:
            m = str(e)
            if "PerDay" in m or "per day" in m.lower() or "API key not valid" in m or "API_KEY_INVALID" in m or "PERMISSION_DENIED" in m or "403" in m[:20]:
                with _kl: _dead.add(i); open(_DF, "a").write(f"{i}\n")
                print("key", i + 1, "dropped:", m[:100].replace("\n", " "), flush=True)
            elif any(s in m for s in ("429", "RESOURCE_EXHAUSTED", "503", "500", "UNAVAILABLE", "disconnected", "Connection", "RemoteProtocol")) or "timed out" in m.lower():
                time.sleep(8 + 4 * (attempt % 6))
            else: return "ERROR: " + m
    return "ERROR: retries exhausted"
def num(s):
    m = re.search(r"(\d+(?:\.\d+)?)", s or ""); return float(m.group(1)) if m else None
def parse_trust(text):
    r = {"pred_score": None, "confidence": None, "evidence": None, "reasoning": None}
    for line in text.strip().splitlines():
        u = line.upper()
        if u.startswith("SCORE:"): r["pred_score"] = num(line)
        elif u.startswith("CONFIDENCE:"):
            v = num(line); r["confidence"] = None if v is None else min(1.0, max(0.0, v))
        elif u.startswith("EVIDENCE:"): r["evidence"] = line.split(":", 1)[1].strip()
        elif u.startswith("REASONING:"): r["reasoning"] = line.split(":", 1)[1].strip()
    return r
def parse_3b(text):
    r = {"mcq_score": None, "short_score": None, "pred_score": None, "confidence": None, "reasoning": None}
    for line in text.strip().splitlines():
        u = line.upper().strip()
        if u.startswith("MCQ_SCORE:"): r["mcq_score"] = num(line)
        elif u.startswith("SHORT_SCORE:"): r["short_score"] = num(line)
        elif u.startswith("TOTAL:"): r["pred_score"] = num(line)
        elif u.startswith("CONFIDENCE:"):
            v = num(line); r["confidence"] = None if v is None else min(1.0, max(0.0, v))
        elif u.startswith("REASONING:"): r["reasoning"] = line.split(":", 1)[1].strip()
    return r
if __name__ == "__main__":
    mode, run = sys.argv[1], sys.argv[2]; budget = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
    rows = list(csv.DictReader(open(D/"Teacher_manual_marks_Anonymized.csv")))
    recs = [{"record_id": f"MDLY-{int(r['Student_ID'].split('_')[1]):04d}", "student": int(r["Student_ID"].split("_")[1]), "teacher_score": float(r["total"])} for r in rows]
    out = HERE/"outputs"/run; out.mkdir(parents=True, exist_ok=True); path = out/f"{mode}_predictions.jsonl"; path.touch()
    done = {json.loads(l)["record_id"] for l in open(path) if l.strip()}
    todo = [r for r in recs if r["record_id"] not in done]; lock = threading.Lock(); deadline = time.time() + budget
    GP = grade_prompt() if mode == "e3b" else None
    def work(r):
        if time.time() > deadline: return
        t0 = time.perf_counter()
        if mode == "m1t3":
            raw = call(render_masked(r["student"]), GRADING_PROMPT); row = {"pred_score": None if raw.startswith("ERROR") else num(raw)}
        elif mode == "m1t5":
            raw = call(render_masked(r["student"]), TRUST_PROMPT); row = {} if raw.startswith("ERROR") else parse_trust(raw)
        elif mode == "e1t3":
            raw = call(render(r["student"], [0]), GRADING_PROMPT); row = {"pred_score": None if raw.startswith("ERROR") else num(raw)}
        elif mode == "e1t5":
            raw = call(render(r["student"], [0]), TRUST_PROMPT); row = {} if raw.startswith("ERROR") else parse_trust(raw)
        else:
            raw = call(render(r["student"], [0, 1, 2, 3]), GP); row = {} if raw.startswith("ERROR") else parse_3b(raw)
        if raw.startswith("ERROR"): print("err", r["record_id"], raw[:110], flush=True); return
        row = {"model": "gemini_3_5_flash", "condition": mode, "record_id": r["record_id"], "true_score": r["teacher_score"], "raw_output": raw, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), **row}
        with lock: open(path, "a").write(json.dumps(row) + "\n")
    with ThreadPoolExecutor(4) as ex: list(ex.map(work, todo))
    print(mode, run, "rows:", sum(1 for _ in open(path)), flush=True)
