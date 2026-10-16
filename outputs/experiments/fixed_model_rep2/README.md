# Fixed-model replication, Run 2
Same protocol as `../fixed_model/` (gemini-3.5-flash, temperature 0, seed 42, 150 DPI page-1 PNG, original prompts, one call per paper per track, 50 Mendeley papers), run on a later day. Produced with `experiments/run_fixed_gemini.py` (output directory via FIXED_OUT).
Files: track3_predictions.jsonl, track5_predictions.jsonl, track3_results_boot.csv, track5_sensitivity.csv, repeat_comparison.csv (Run 1 vs Run 2 metrics), cross_track_ocr_legibility.csv.
Track 3 MAE 0.80, r 0.981; Track 5 AUROC 0.621 [0.435, 0.813]. Predictions equal Run 1 on 47/50 (Track 3) and 49/50 (Track 5) papers.
