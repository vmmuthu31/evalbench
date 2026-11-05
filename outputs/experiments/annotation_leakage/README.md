# Annotation-leakage experiment (run 1)
Same model/settings as the fixed-model runs (gemini-3.5-flash, temp 0, seed 42), but on the raw, unannotated Student_Pdf scans of the Mendeley dataset.
| Condition | n | MAE | r |
|---|---|---|---|
| Annotated page 1 (teacher's circled total visible), Track 3 | 50 | 1.58 | 0.873 |
| Clean page 1, Track 3 | 50 | 9.68 | 0.220 |
| Clean page 1, Track 5 (AUROC 0.613, ECE 0.337) | 50 | 9.44 | 0.293 |
| Independent grading, 4 pages + key + rubric (3b) | 50 | 4.17 | 0.829 |
| Mean-predictor baseline | 50 | 5.81 | - |
Run 2 pending (free-tier quota). Reproduce: set GEMINI_KEYS_FILE, MENDELEY_DIR, run `run_masked.py <e1t3|e1t5|e3b> run1`, then `analyse.py`.
