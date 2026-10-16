"""Controlled replication of Tracks 3 and 5 with ONE fixed model version.
Model: gemini-3.5-flash, temperature 0, seed 42, 150 DPI page-1 PNG, original prompts.
Usage: GEMINI_KEYS_FILE=<file with one API key per line> python3 experiments/run_fixed_gemini.py [track3|track5] [seconds_budget]
Keys are tried in order; a key is dropped when its daily quota is exhausted or it is rejected.
Outputs go to outputs/experiments/$FIXED_OUT (default fixed_model; use e.g. FIXED_OUT=fixed_model_rep2 for a repeat run) (original pooled outputs are not touched)."""
import sys, os, io, json, time, importlib.util
from pathlib import Path
ROOT = Path(__file__).parent.parent
def load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
t3 = load("t3", "experiments/track3_assessment/run_assessment_eval.py")
t5 = load("t5", "experiments/track5_trust/run_trust_eval.py")
from google import genai as gai
from google.genai import types as gt
MODEL, OUT = "models/gemini-3.5-flash", ROOT / "outputs/experiments" / os.environ.get("FIXED_OUT", "fixed_model"); OUT.mkdir(parents=True, exist_ok=True)
import threading
KEYS = [k.strip() for k in open(os.environ["GEMINI_KEYS_FILE"]) if k.strip()]
_klock = threading.Lock()
_DF = os.path.join(os.path.dirname(os.environ["GEMINI_KEYS_FILE"]), ".gemini_dead_" + time.strftime("%Y%m%d", time.gmtime()))
_dead = set(int(x) for x in open(_DF).read().split()) if os.path.exists(_DF) else set()
def _key():
    with _klock:
        for i, k in enumerate(KEYS):
            if i not in _dead: return i
    return None
cfg = gt.GenerateContentConfig(temperature=0.0, seed=42)
def call(img, prompt):
    buf = io.BytesIO(); img.save(buf, format="PNG")
    for attempt in range(40):
        i = _key()
        if i is None: return "ERROR: all keys exhausted"
        try:
            c = gai.Client(api_key=KEYS[i])
            return c.models.generate_content(model=MODEL, contents=[gt.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"), prompt], config=cfg).text.strip()
        except Exception as e:
            m = str(e)
            if "PerDay" in m or "per day" in m.lower() or "API key not valid" in m or "API_KEY_INVALID" in m or "PERMISSION_DENIED" in m or "403" in m[:20]:
                with _klock:
                    _dead.add(i); open(_DF, 'a').write(f'{i}\n')
                print("key", i + 1, "dropped:", m[:90].replace("\n", " "), flush=True)
            elif "429" in m or "RESOURCE_EXHAUSTED" in m or "503" in m or "500" in m or "UNAVAILABLE" in m or "disconnected" in m or "timed out" in m.lower() or "Connection" in m or "RemoteProtocol" in m:
                time.sleep(10 + 5 * (attempt % 6))
            else: return "ERROR: " + m
    return "ERROR: retries exhausted"
which = sys.argv[1]; budget = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9
recs = [json.loads(l) for l in open(ROOT/'datasets/processed/mendeley_records.jsonl')]
path = OUT / f"{which}_predictions.jsonl"; path.touch()
done = {json.loads(l)["record_id"] for l in open(path) if l.strip()}
todo = [r for r in recs if r["record_id"] not in done]
from concurrent.futures import ThreadPoolExecutor
lock = threading.Lock(); deadline = time.time() + budget
def work(r):
    if time.time() > deadline: return
    img = t3.pdf_to_image(ROOT / r["image_path"]); t0 = time.perf_counter()
    if which == "track3":
        raw = call(img, t3.GRADING_PROMPT); row = {"pred_score": t3.parse_score(raw) if not raw.startswith("ERROR") else None}
    else:
        raw = call(img, t5.TRUST_PROMPT); parsed = {} if raw.startswith("ERROR") else t5.parse_trust_response(raw)
        row = {k: parsed.get(k) for k in ("pred_score", "confidence", "evidence", "reasoning")}
    if raw.startswith("ERROR"): print("err", r["record_id"], raw[:100], flush=True); return
    row = {"model": "gemini_3_5_flash", "record_id": r["record_id"], "true_score": r["teacher_score"], "raw_output": raw, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), **row}
    with lock: open(path, "a").write(json.dumps(row) + "\n")
with ThreadPoolExecutor(4) as ex: list(ex.map(work, todo))
print(which, "done rows:", sum(1 for _ in open(path)), flush=True)
