# EvalBench v1 (Pilot Release) — Leaderboard

Results as reported in the manuscript. Bootstrap confidence intervals are 95%, 10,000 resamples,
seed 42. Raw per-record predictions backing these numbers are in `data/results/`.

## Track 1 — OCR (IAM / IIIT English Word test splits)

| Model | IAM CER | IAM EM | IAM CharAcc | IIIT-W CER | IIIT-W EM | IIIT-W CharAcc |
|---|---|---|---|---|---|---|
| Tesseract 5 | 0.798 | 0.045 | 0.202 | 0.662 | 0.148 | 0.338 |
| EasyOCR | 0.631 | 0.045 | 0.369 | 0.372 | 0.296 | 0.628 |
| TrOCR-base | 0.229 | 0.553 | 0.771 | 0.522 | 0.291 | 0.478 |
| PaddleOCR | 0.513 | 0.075 | 0.487 | 0.177 | 0.664 | 0.823 |

n = 199 (IAM) / 223 (IIIT-Word) for Tesseract 5, EasyOCR, and TrOCR-base; n = 133 (IAM) / 146
(IIIT-Word) for PaddleOCR, which was evaluated in a separate batch with a smaller sample cap — see
the manuscript's Section 4.2 and Limitations for the operational reason and its implications.

Headline finding: OCR model rankings **fully reverse** between the two corpora. TrOCR-base leads
on IAM (EM = 0.553) but drops to third on IIIT-Word (EM = 0.291); PaddleOCR leads on IIIT-Word
(EM = 0.664) but is near-bottom on IAM (EM = 0.075). All four cross-corpus EM gaps are
statistically significant (paired bootstrap + permutation test, p < 0.001, except Tesseract 5 at
p = 0.0005).

## Track 3 — Educational Assessment (Mendeley, n = 50)

| Model | MAE | Pearson r | Spearman rho | EM±1 | EM±5 |
|---|---|---|---|---|---|
| Gemini (combined, no rubric) | 3.780 | 0.543 | 0.550 | 0.580 | 0.780 |

95% CI: MAE [2.090, 5.730], Pearson r [0.235, 0.801]. Graded with no rubric provided (zero-shot
holistic scoring); see manuscript Section 6.3 for the mixed-Gemini-variant caveat before treating
this as a fixed-model result.

## Track 5 — Trustworthiness (Mendeley, n = 50)

| Model | ECE | AUROC | Evidence Generation Rate | Reasoning Rate | MAE |
|---|---|---|---|---|---|
| Gemini (combined) | 0.251 | 0.571 | 1.000 | 1.000 | 4.120 |

95% CI: AUROC [0.320, 0.680], ECE [0.129, 0.376]. AUROC near 0.5 (chance) means stated confidence
carries almost no signal about whether the score is correct, despite a perfect Evidence Generation
Rate (a prompt-compliance presence check, not a verified-support metric — see `docs/TRACKS.md`).

## Tracks 2 and 4

No baseline yet — schema-defined only in this pilot release. Contributions welcome; see the main
README's Roadmap section.

## Submitting a result

This pilot release does not yet have an automated submission/leaderboard pipeline. To propose a
new result, open a PR adding a row to the relevant table above with a link to your raw predictions
in the same schema as `data/results/`, or open an issue describing your setup.
