"""Run the annotation-leakage conditions with an open-weight VLM served by Ollama (e.g. qwen2.5vl:7b on an M-series Mac).
Same prompts, pages and page rendering as run_masked.py (Gemini), so results are directly comparable.
Conditions: a1t3 annotated page 1 | e1t3 clean page 1 | e1t5 clean page 1 + confidence | e3b clean 4 pages + key + rubric.
Setup (Mac, 16 GB is enough for the 7B model):
  ollama pull qwen2.5vl:7b          # ~6 GB
  pip3 install pymupdf pillow
  export MENDELEY_DIR="/path/to/A Dataset of Digitized Student Examination Papers,"
  python3 run_ollama.py a1t3 run1 && python3 run_ollama.py e1t3 run1 && python3 run_ollama.py e1t5 run1 && python3 run_ollama.py e3b run1
  (repeat everything with run2 for a second run; resumable, safe to Ctrl-C and restart)
Decoding: temperature 0, seed 42. Output: outputs/ollama_<model>_<run>/<mode>_predictions.jsonl"""
import ast, sys, os, json, csv, time, base64, io, urllib.request
from pathlib import Path
HERE = Path(__file__).parent
_tree = ast.parse((HERE / "run_masked.py").read_text())
_keep = {"GRADING_PROMPT", "TRUST_PROMPT"}; _fn = {"grade_prompt", "num", "parse_trust", "parse_3b", "render"}
_body = [n for n in _tree.body if (isinstance(n, ast.Assign) and any(getattr(t, "id", None) in _keep | {"D"} for t in n.targets))
         or (isinstance(n, ast.FunctionDef) and n.name in _fn)
         or (isinstance(n, (ast.Import, ast.ImportFrom)) and "genai" not in ast.dump(n) and "google" not in ast.dump(n))]
ns = {"__file__": str(HERE / "run_masked.py")}; exec(compile(ast.Module(_body, []), "subset", "exec"), ns)
D, GRADING_PROMPT, TRUST_PROMPT = ns["D"], ns["GRADING_PROMPT"], ns["TRUST_PROMPT"]
grade_prompt, num, parse_trust, parse_3b, render0 = ns["grade_prompt"], ns["num"], ns["parse_trust"], ns["parse_3b"], ns["render"]
import fitz
from PIL import Image
def render_annotated(student, pages, width=1240):
    out = []; doc = fitz.open(str(D / "Corrected_Pdf" / f"Student_{student}.pdf"))
    for p in [q for q in pages if q < len(doc)]:
        pg = doc.load_page(p); z = width / pg.rect.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(z, z)); out.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
    doc.close(); return out
def b64(im):
    b = io.BytesIO(); im.save(b, format="PNG"); return base64.b64encode(b.getvalue()).decode()
def chat(model, prompt, imgs, ctx):
    body = {"model": model, "stream": False, "messages": [{"role": "user", "content": prompt, "images": [b64(i) for i in imgs]}],
            "options": {"temperature": 0, "seed": 42, "num_ctx": ctx, "num_predict": 200}}
    req = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=900).read())["message"]["content"].strip()
def main():
    mode, run = sys.argv[1], sys.argv[2]; model = sys.argv[3] if len(sys.argv) > 3 else "qwen2.5vl:7b"
    rows = list(csv.DictReader(open(D / "Teacher_manual_marks_Anonymized.csv")))
    recs = sorted(({"record_id": f"MDLY-{int(r['Student_ID'].split('_')[1]):04d}", "student": int(r["Student_ID"].split("_")[1]), "teacher_score": float(r["total"])} for r in rows), key=lambda r: r["record_id"])
    out = HERE / "outputs" / f"ollama_{model.replace(':','_').replace('/','_')}_{run}"; out.mkdir(parents=True, exist_ok=True)
    path = out / f"{mode}_predictions.jsonl"; path.touch(); done = {json.loads(l)["record_id"] for l in open(path) if l.strip()}
    GP = grade_prompt() if mode == "e3b" else None
    for r in recs:
        if r["record_id"] in done: continue
        if mode == "a1t3": imgs, prompt, ctx = render_annotated(r["student"], [0]), GRADING_PROMPT, 8192
        elif mode == "e1t3": imgs, prompt, ctx = render0(r["student"], [0]), GRADING_PROMPT, 8192
        elif mode == "e1t5": imgs, prompt, ctx = render0(r["student"], [0]), TRUST_PROMPT, 8192
        else: imgs, prompt, ctx = render0(r["student"], [0, 1, 2, 3]), GP, 16384
        t0 = time.perf_counter()
        try: raw = chat(model, prompt, imgs, ctx)
        except Exception as e: print("err", r["record_id"], str(e)[:100], flush=True); continue
        row = {"pred_score": num(raw)} if mode in ("a1t3", "e1t3") else (parse_trust(raw) if mode == "e1t5" else parse_3b(raw))
        row = {"model": model, "condition": mode, "record_id": r["record_id"], "true_score": r["teacher_score"], "raw_output": raw, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), **row}
        open(path, "a").write(json.dumps(row) + "\n"); print(r["record_id"], row.get("pred_score"), flush=True)
    print(mode, run, "rows:", sum(1 for _ in open(path)))
if __name__ == "__main__": main()
