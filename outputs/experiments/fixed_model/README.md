# Fixed-model replication (Tracks 3 and 5)
One model version (gemini-3.5-flash), temperature 0, seed 42, 150 DPI page-1 PNG, the original prompts,
all 50 Mendeley papers in both tracks. Produced with `experiments/run_fixed_gemini.py`.
The original mixed-version outputs in `../track3` and `../track5` are untouched.
Files: track3_predictions.jsonl / track5_predictions.jsonl (raw), track3_results.csv, track5_results.csv,
track5_sensitivity.csv (correctness tolerance +-1..10 marks; AUROC with mid-ranks, ECE, Brier; bootstrap 95% CIs, 10,000 resamples, seed 42).
Note: Gemini outputs are not guaranteed bit-reproducible even at temperature 0; two calls on the same paper (one per track) can differ.

Run 2 (identical settings, repeated later) is in `../fixed_model_rep2/`; compare with `experiments/compare_repeat_runs.py`. Track 3 MAE 1.58 (Run 1) vs 0.80 (Run 2); Track 5 AUROC 0.530 vs 0.621. Treat this directory as Run 1.
