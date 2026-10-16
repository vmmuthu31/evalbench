"""OCR.space evaluation on the matched Track 1 records (same records PaddleOCR processed).
Usage: OCRSPACE_API_KEY=... python3 experiments/ocr/run_ocrspace.py ENGINE [budget_seconds]
Writes outputs/experiments/ocr/ocrspace_engine{N}_predictions.jsonl (resumable)."""
import sys, os, json, time, threading, mimetypes, requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "experiments" / "ocr"))
from metrics import compute_all
ENGINE = int(sys.argv[1]); budget = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9
KEY = os.environ["OCRSPACE_API_KEY"]; name = f"ocrspace_e{ENGINE}"
pred = [json.loads(l) for l in open(ROOT / "outputs/experiments/ocr/predictions.jsonl")]
ids = {r["record_id"] for r in pred if r["model"] == "paddleocr" and r["dataset"] in ("iam", "iiit_word") and len(r["ref"].strip()) >= 3}
meta = {}
for ds in ("iam", "iiit_word"):
    for l in open(ROOT / f"datasets/processed/{ds}_records.jsonl"):
        r = json.loads(l)
        if r["record_id"] in ids: meta[r["record_id"]] = r
out = ROOT / f"outputs/experiments/ocr/ocrspace_engine{ENGINE}_predictions.jsonl"; out.touch()
done = {json.loads(l)["record_id"] for l in open(out) if l.strip()}
todo = [meta[i] for i in sorted(ids) if i not in done]; lock = threading.Lock(); deadline = time.time() + budget
def work(r):
    if time.time() > deadline: return
    p = ROOT / r["image_path"]; t0 = time.perf_counter(); text = None
    for attempt in range(3):
        try:
            with open(p, "rb") as fh:
                resp = requests.post("https://api.ocr.space/parse/image", headers={"apikey": KEY}, files={"file": (p.name, fh, mimetypes.guess_type(p.name)[0] or "image/png")}, data={"language": "eng", "OCREngine": ENGINE, "scale": "false"}, timeout=40).json()
            if "error" in resp and "ParsedResults" not in resp: print("API ERROR", str(resp)[:150], flush=True); return
            if resp.get("IsErroredOnProcessing"):
                msg = str(resp.get("ErrorMessage"))
                if "limit" in msg.lower() or "too many" in msg.lower(): print("LIMIT", msg[:120], flush=True); return
                text = ""; break
            text = " ".join((x.get("ParsedText") or "").strip() for x in resp.get("ParsedResults", [])).strip(); break
        except Exception as e:
            time.sleep(3)
    if text is None: print("fail", r["record_id"], flush=True); return
    m = compute_all(text, r["ocr_text"])
    row = {"model": name, "record_id": r["record_id"], "dataset": r["dataset"], "pred": text, "ref": r["ocr_text"], "latency_ms": round((time.perf_counter() - t0) * 1000, 2), "mem_kb": 0.0, **m}
    with lock: open(out, "a").write(json.dumps(row) + "\n")
with ThreadPoolExecutor(4) as ex: list(ex.map(work, todo))
print(name, "rows:", sum(1 for _ in open(out)), "of", len(ids), flush=True)
