# Annotation-leakage experiment (run 1)
Same model/settings as the fixed-model runs (gemini-3.5-flash, temp 0, seed 42), but on the raw, unannotated Student_Pdf scans of the Mendeley dataset.
| Condition | n | MAE | r |
|---|---|---|---|
| Annotated page 1 (teacher's circled total visible), Track 3 | 50 | 1.58 | 0.873 |
| Clean page 1, Track 3 | 50 | 9.68 | 0.220 |
| Clean page 1, Track 5 (AUROC 0.613, ECE 0.337) | 50 | 9.44 | 0.293 |
| Independent grading, 4 pages + key + rubric (3b) | 50 | 4.17 | 0.829 |
| Mean-predictor baseline | 50 | 5.81 | - |
Run 2 (same settings, independent calls): clean T3 MAE 10.26 [8.64, 11.94], r 0.275; clean T5 MAE 8.76, AUROC 0.494, ECE 0.348, 22% within 3; independent grading MAE 3.94 [2.95, 5.03], r 0.822, mean confidence 0.95 vs 56% within 3 (ECE 0.390, AUROC 0.500). Run-to-run: clean T3 r 0.38 (24/50 identical), independent grading r 0.99 (25/50 identical). Reproduce: set GEMINI_KEYS_FILE, MENDELEY_DIR, run `run_masked.py <e1t3|e1t5|e3b> run1`, then `python analyse.py outputs/experiments/annotation_leakage/run1/` (or run2/).

## Qwen2.5-VL-7B (Ollama, one run, n=50)
| Condition | MAE | r | Note |
|---|---|---|---|
| Annotated page 1, Track 3 | 5.48 | 0.42 | cannot read the circled total (mean predictor 5.81) |
| Clean page 1, Track 3 | 6.44 | 0.13 | |
| Clean page 1, Track 5 | 9.40 | -0.03 | AUROC 0.507, mean confidence 0.68 |
| Independent grading (4 pages + key) | 17.72 | 0.04 | predicts ~46 for all, mean confidence 0.95, 1/50 within 3 marks |
Runner and prompts: run_ollama.py (on the author's machine; add to repo if wanted).
