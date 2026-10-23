# Changelog

EvalBench uses [GitHub Releases](https://github.com/vmmuthu31/evalbench/releases) (tied to git
tags) rather than a `releases/` folder in the repository tree, so that release assets and notes
stay attached to a specific commit and don't bloat the working tree. This file summarizes what
changed at each tag.

## v1.0.0-pilot — 2026-08-03

Initial public release, matching the manuscript *"EvalBench v1 (Pilot Release): A Unified
Multi-Task Benchmark for AI Evaluation in Educational Settings."*

- 132,891-record processed corpus across six source datasets (`data/processed/evalbench_v1.jsonl`)
- EvalBench JSON Schema v2.0 (`schema/schema.json`), defining all five tracks
- Track 1 (OCR), Track 3 (Educational Assessment), and Track 5 (Trustworthiness) evaluation
  harnesses, raw predictions, and statistically supported results (bootstrap CIs, permutation
  tests)
- Tracks 2 (Document Understanding) and 4 (Multimodal Understanding) specified in the schema but
  not yet experiment-ready — no labelled ground truth or baseline script in this release

## Unreleased — 2026-10-23

- Reframed Tracks 3 and 5 as score recovery from annotated scripts (the teacher's circled total is
  visible on page 1; evidence cites a circled/red-ink mark in 48/50 and 47/50 responses). Wording
  only: no predictions, metrics or code behaviour changed.
- Documented that the ledger reference total can differ from the circled total.

## Planned for v1.1.0

- Track 2 baseline using the currently-unlabelled `anshcode1` records once annotated
- Acquisition of the IEEE Answer Sheet Dataset referenced by the schema for Tracks 2/3/4/5
- Re-run of Tracks 3 and 5 on a single fixed Gemini model version, removing the mixed-variant
  confound disclosed in the manuscript's Limitations
- Matched sample size for PaddleOCR in Track 1 (currently evaluated on ~2/3 the sample of the
  other three OCR models)

## Planned for v2.0.0

- Track 4 baseline (multimodal / diagram interpretation)
- Expansion of the graded-assessment corpus beyond the current 50 Mendeley papers
- Additional languages beyond English

## Repeat-run update — 2026-10-16

Archived on Zenodo as https://doi.org/10.5281/zenodo.23410592.

- Track 3 and Track 5 fixed-model evaluation run a second time under identical settings
  (`outputs/experiments/fixed_model_rep2/`); Run 1 stays in `outputs/experiments/fixed_model/`.
  Track 3 MAE 1.58 (Run 1) vs 0.80 (Run 2); Track 5 AUROC 0.530 vs 0.621, both CIs include 0.5.
- New scripts: `scripts/experiments/run_fixed_gemini.py` (key-rotating, resumable runner;
  `FIXED_OUT` selects the output folder), `compare_repeat_runs.py`, `track3_bootstrap_stats.py`,
  `track5_trust/track5_sensitivity.py`.
- Leaderboard lists both runs.
- Bootstrap intervals now use one documented procedure (`scripts/experiments/canonical_bootstrap.py`: records sorted by `record_id`,
  numpy `default_rng(42)`, 10,000 resamples). `track3_bootstrap_stats.py` and `track5_trust/track5_sensitivity.py` use it, and the CSVs
  `track3_results_boot.csv`, `track5_sensitivity.csv` and `bootstrap_canonical.csv` were regenerated; point estimates are unchanged and
  interval end-points moved by at most 0.05 (Track 3/5 only; Track 1 and Track 2 intervals were already identical).
