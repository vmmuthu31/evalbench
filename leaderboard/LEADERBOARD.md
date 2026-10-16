# EvalBench v1 (Pilot Release) — Leaderboard

Results as reported in the manuscript. Bootstrap confidence intervals are 95%, 10,000 resamples,
seed 42. Raw per-record predictions backing these numbers are in `data/results/`.

## Systems supported by the evaluation harness

Every system below is wired into the evaluation harness under the same `OCRModel` interface (see
`scripts/experiments/ocr/models/`) or, for Gemini, the same Track 3/5 prompt-and-parse pipeline.
"Reported" means results are in this pilot release; "Integrated, v1.1" means the code runs today
but hasn't been evaluated on the full test split yet (mainly due to free-tier API request caps —
see the Quick Start below to run them yourself).

| Model | Type | Open | Free | Offline | Track(s) | Status (v1) |
|---|---|---|---|---|---|---|
| Tesseract 5 | Classical OCR | Yes | Yes | Yes | OCR | Reported |
| EasyOCR | Deep-learning OCR | Yes | Yes | Yes | OCR | Reported |
| TrOCR-base | Transformer OCR | Yes | Yes | Yes | OCR | Reported |
| PaddleOCR | Deep-learning OCR | Yes | Yes | Yes | OCR | Reported |
| OCR.space | Hosted OCR API | No | Yes (free tier) | No | OCR | Integrated, v1.1 |
| Optiic | Hosted OCR API | No | Yes (free tier) | No | OCR | Integrated, v1.1 |
| API Ninjas | Hosted OCR API | No | Yes (free tier) | No | OCR | Integrated, v1.1 |
| Florence-2 | Vision-language model | Yes | Yes | Yes | Document Understanding, OCR | Reported (Track 2) |
| Qwen2.5-VL | Vision-language model | Yes | Yes | Yes | OCR | Integrated, v1.1 |
| Gemini Flash | Proprietary VLM | No | Yes (free tier) | No | Grading, Trust | Reported |

Run the free-tier OCR APIs yourself:

```bash
export OCRSPACE_API_KEY=...   # https://ocr.space/ocrapi/freekey
export OPTIIC_API_KEY=...     # https://optiic.dev/signup
export API_NINJAS_KEY=...     # https://api-ninjas.com/
python3 scripts/experiments/ocr/run_ocr_eval.py --models ocrspace optiic apininjas --n 200
```

## Track 1 — OCR (IAM / IIIT English Word test splits)

| Model | IAM CER | IAM EM | IAM CharAcc | IIIT-W CER | IIIT-W EM | IIIT-W CharAcc |
|---|---|---|---|---|---|---|
| Tesseract 5 | 0.784 | 0.045 | 0.268 | 0.663 | 0.164 | 0.404 |
| EasyOCR | 0.638 | 0.053 | 0.362 | 0.395 | 0.247 | 0.624 |
| TrOCR-base | 0.224 | 0.534 | 0.782 | 0.509 | 0.301 | 0.569 |
| PaddleOCR | 0.513 | 0.075 | 0.493 | 0.176 | 0.664 | 0.827 |
| OCR.space (hosted, Engine 2) | 0.257 | 0.571 | 0.743 | 0.322 | 0.514 | 0.697 |

All five systems are scored on the same records: n = 133 (IAM) / 146 (IIIT-Word), the records that
PaddleOCR also processed. OCR.space was queried through its free hosted API on 2026-10-12 with the
default Engine 2 (Engine 3 was not run: free-tier limit of 60 requests/hour). CER is Levenshtein
distance divided by reference length (it can exceed 1); Character Accuracy is max(0, 1 - CER) per
record, averaged. Larger unmatched runs (n = 199 / 223 for Tesseract 5, EasyOCR and TrOCR-base) are in
the released per-record predictions.

Headline finding: the best OCR system changes between the two corpora. OCR.space leads on IAM
(EM = 0.571) but is second on IIIT-Word (EM = 0.514); PaddleOCR leads on IIIT-Word (EM = 0.664) but is
third on IAM (EM = 0.075). EasyOCR (4th) and Tesseract 5 (5th) hold on both. Four of five cross-corpus
EM gaps are significant (independent-samples bootstrap + permutation test, p < 0.001, except Tesseract 5
at p = 0.002); OCR.space's gap (+0.058, 95% CI -0.056 to +0.171, p = 0.345) is not.

## Track 2 — Document Understanding (IIIT English Page, page-level, n = 50)

| Model | CER | WER | Exact Match | Character Accuracy |
|---|---|---|---|---|
| Tesseract 5 | 6.044 | 11.489 | 0.000 | 0.233 |
| Florence-2-base | 0.180 | 0.580 | 0.000 | 0.820 |

95% CI: Tesseract 5 CER [3.681, 8.740], CharAcc [-7.708, -2.665]; Florence-2-base CER [0.149,
0.220], CharAcc [0.782, 0.852]. Both models evaluated on the identical 50 test-split records.

Headline finding: the two baselines diverge sharply on the same pages. Tesseract 5, a classical
non-handwriting-specialised engine, fails catastrophically on cursive multi-line page scans
(CER > 600%, driven by long runs of spurious inserted characters); Florence-2-base, an open
vision-language model, handles the same pages competently (CharAcc = 0.820) without any
page-specific tuning. Exact Match is 0.000 for both, since a single character error anywhere in a
full page fails a whole-page criterion — EM is not an informative headline metric at this
granularity. See manuscript Section 4.3.

## Track 3 — Educational Assessment (Mendeley, n = 50)

| Model | MAE | Pearson r | Spearman rho | EM±1 | EM±5 |
|---|---|---|---|---|---|
| gemini-3.5-flash (fixed version, no rubric), Run 1 | 1.580 | 0.873 | 0.896 | 0.720 | 0.920 |
| gemini-3.5-flash (fixed version, no rubric), Run 2 | 0.800 | 0.981 | 0.977 | 0.760 | 0.980 |
| *Earlier mixed-version run (superseded)* | 3.780 | 0.543 | 0.550 | 0.580 | 0.780 |

95% CI (Run 1): MAE [0.690, 2.700], Pearson r [0.697, 0.981], Spearman rho [0.704, 0.988]; 88% of papers within ±3 marks. Run 2 (identical settings): MAE [0.460, 1.190], Pearson r [0.964, 0.992]; 92% within ±3 marks. The runs agree on 47 of 50 papers; the three that differ (Run 1 errors of 14, 8 and 21 marks) carry 43 of Run 1's 79 total absolute-error marks, so a single call's MAE can halve on repetition. Report both runs.
Fixed run: temperature 0, seed 42, 150 DPI page-1 PNG, one call per paper (`outputs/experiments/fixed_model/`). The earlier run
split the papers across three Gemini variants (per-variant MAE 1.43–6.17) and cannot separate model from paper subset.

## Track 5 — Trustworthiness (Mendeley, n = 50)

| Model | ECE | AUROC | Brier | Evidence Generation Rate | Reasoning Rate | MAE |
|---|---|---|---|---|---|---|
| gemini-3.5-flash (fixed version), Run 1 | 0.106 | 0.530 | 0.144 | 1.000 | 1.000 | 1.840 |
| gemini-3.5-flash (fixed version), Run 2 | 0.115 | 0.621 | 0.155 | 1.000 | 1.000 | 2.040 |
| *Earlier mixed-version run (superseded)* | 0.251 | 0.506 | 0.266 | 1.000 | 1.000 | 4.120 |

95% CI (Run 1): AUROC [0.380, 0.701], ECE [0.017, 0.208], Brier [0.058, 0.234]. Brier 0.144 is no better than the 0.134 obtained by
always stating the 84% base rate. Mean stated confidence is 0.940 for the 42 correct and 0.938 for the 8 incorrect grades (±3 marks): stated
confidence carries no usable signal despite a perfect Evidence Generation Rate (a prompt-compliance presence check, not a
verified-support metric — see `docs/TRACKS.md`). AUROC uses mid-ranks for tied confidences; an earlier script version resolved ties by sweep
order and reported 0.571 for the mixed run (corrected: 0.506). Tolerance sensitivity (±1 to ±10 marks, AUROC 0.46–0.57, every CI contains 0.5):
`outputs/experiments/fixed_model/track5_sensitivity.csv`.
Run 2: AUROC [0.433, 0.810], ECE [0.019, 0.226], Brier [0.070, 0.248] (Brier 0.155 vs 0.148 for the 82% base rate); both AUROC intervals include 0.5. Sensitivity: `outputs/experiments/fixed_model_rep2/track5_sensitivity.csv`. Run comparison: `outputs/experiments/fixed_model_rep2/repeat_comparison.csv`.

## Track 4

No baseline yet. Direct inspection of the processed corpus confirms the only currently available
source, gopika13, supplies handwriting images without the paired question-answer annotations
multi-modal question answering requires — this is a labelled-data gap, not an unimplemented
evaluation script. Contributions of a labelled Track 4 source are welcome; see the main README's
Roadmap section.

## Submitting a result

This pilot release does not yet have an automated submission/leaderboard pipeline. To propose a
new result, open a PR adding a row to the relevant table above with a link to your raw predictions
in the same schema as `data/results/`, or open an issue describing your setup.

AUROC uses mid-ranks for tied confidences (the model states only 0.90, 0.95 or 1.00). An earlier script version
resolved ties by sweep order and reported 0.571; the corrected value is 0.506. Tolerance sensitivity
(+-1 to +-10 marks) is in `outputs/experiments/track5/track5_sensitivity.csv`.
