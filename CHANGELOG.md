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
