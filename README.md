# EvalBench

**A unified multi-task benchmark for AI evaluation in educational settings.**

Repository: [github.com/vmmuthu31/evalbench](https://github.com/vmmuthu31/evalbench)

EvalBench is an open research benchmark for evaluating AI systems on educational document analysis
tasks. It provides a unified evaluation framework covering OCR, document understanding, educational
assessment, multimodal understanding, and trustworthiness under a common schema and standardized
evaluation protocol, instead of five separate single-task benchmarks.

This repository hosts the EvalBench benchmark and its reproducibility package. Versioned releases
are available through [GitHub Releases](https://github.com/vmmuthu31/evalbench/releases); see
`CHANGELOG.md` for what changed at each version.

**Current release: v1.0.0-pilot**, the reproducibility package for the manuscript *"EvalBench v1
(Pilot Release): A Unified Multi-Task Benchmark for AI Evaluation in Educational Settings,"*
archived on Zenodo and since updated with a second fixed-model run, the OCR.space baseline and Track 2 results.

Status: Pilot Release (v1.0.0)
Archive: Zenodo (cite the version DOI shown on the record; the record lists both authors)
License: MIT (code), CC BY 4.0 (processed manifest)

## What this pilot release reports

Five tracks are defined in the schema; four have experimental results in this release:

- **OCR accuracy (Track 1).** Performance for five OCR systems — Tesseract 5, EasyOCR, TrOCR-base, PaddleOCR and the
  hosted OCR.space API (Engine 2) — on records matched across all five systems (133 IAM and 146 IIIT English Word),
  with bootstrap confidence intervals and permutation tests on the cross-corpus rank reversal.
- **Document understanding (Track 2, preliminary).** Page-level OCR on 50 IIIT English Page records: Tesseract 5 (CER 6.044) and
  Florence-2-base (CER 0.180).
- **Educational assessment (Track 3).** Score recovery from annotated scripts: a Gemini model reads the teacher's recorded total on 50 Mendeley exam
  papers with one fixed Gemini version (gemini-3.5-flash, temperature 0, seed 42), run twice (MAE 1.58 and 0.80 marks), with bootstrap CIs on MAE and Pearson r.
- **Trustworthiness (Track 5).** Confidence calibration (ECE, AUROC) and evidence-generation rate
  on the same 50 papers, also run twice (AUROC 0.530 and 0.621; both CIs include 0.5).

Caveat: the teacher's circled total is visible on page 1 of the Mendeley scripts, and the model's own evidence cites a circled or red-ink mark in 48/50 (Run 1) and 47/50 (Run 2) responses. Tracks 3 and 5 therefore measure score recovery (reading a recorded total from an annotated script) and confidence in that reading, not independent grading. The reference total is the ledger value, which can differ from the circled total (e.g. MDLY-0008: circled 27, ledger 25).

Track 4 (multimodal understanding) is specified in the schema but has no evaluable labelled data in this release
(gopika13 has no paired question-answer annotations) — see the manuscript's Limitations and Future Work sections.

`python3 scripts/verify_reported_tables.py` recomputes the Track 1, 2, 3 and 5 numbers in the manuscript from the archived
predictions in `outputs/experiments/`. The aggregate record count (132,891) is dominated by word-level OCR crops; the
assessment and trustworthiness tracks rest on 50 papers.

## Repository layout

```
schema/                          EvalBench JSON Schema v2.0 (record and track definitions)
data/processed/                  Processed corpus manifest (evalbench_v1.jsonl, 132,891 records)
data/results/ocr/                Raw per-record OCR predictions (all 4 models)
data/results/track3/             Raw per-record Track 3 score-recovery predictions
data/results/track5/             Raw per-record Track 5 trustworthiness predictions
scripts/experiments/ocr/         OCR evaluation harness + model wrappers + metrics
scripts/experiments/track3_assessment/   Track 3 evaluation harness
scripts/experiments/track5_trust/        Track 5 evaluation harness (calibration, evidence rate)
scripts/build/                   Dataset assembly, verification, statistics, and manuscript
                                  build scripts (python-docx)
docs/                             Schema reference and per-track documentation
examples/                         Minimal usage examples (e.g. loading the manifest)
leaderboard/                      Current results table and how to submit a new one
CHANGELOG.md                      What changed at each version (see also GitHub Releases)
```

## Quick start

```bash
git clone https://github.com/vmmuthu31/evalbench.git
cd evalbench
python3 examples/load_dataset.py --track ocr_substrate --split test
```

See `docs/SCHEMA.md` for the record format, `docs/TRACKS.md` for what each track evaluates, and
`leaderboard/LEADERBOARD.md` for current results.

## Data availability and licensing note

`data/processed/evalbench_v1.jsonl` contains derived annotations (transcriptions, scores, split
assignments, schema-defined fields) for all six constituent datasets, **not** raw images. IAM is
distributed under a license that requires individual registration and restricts redistribution of
its source images, so this repository does not re-host IAM or IIIT English Word images; obtain
those directly from their original sources (cited in the manuscript's reference list and Section
3) and use the `image_path` field to align them with this manifest.

Constituent dataset sources:

- IAM Handwriting Database
- IIIT English Word / Page
- anshcode1 exam-script images (CC BY 4.0)
- Mendeley Graded Exam Papers dataset (Dinesh K. P., 2026, DOI: 10.17632/sf3kvjwknt.1)
- gopika13 answer scripts

## Reproducing the results

```bash
# Rebuild the processed corpus from raw sources (requires raw data_sources/ locally)
python3 scripts/build/build_evalbench.py

# Re-run Track 1 OCR evaluation
python3 scripts/experiments/ocr/run_ocr_eval.py --n 0

# Fixed-model Track 3 / Track 5 run (GEMINI_KEYS_FILE = one API key per line; keys are tried in order).
# Run 1 -> outputs/experiments/fixed_model/, Run 2 -> FIXED_OUT=outputs/experiments/fixed_model_rep2
GEMINI_KEYS_FILE=keys.txt python3 scripts/experiments/run_fixed_gemini.py track3
GEMINI_KEYS_FILE=keys.txt python3 scripts/experiments/run_fixed_gemini.py track5
python3 scripts/experiments/compare_repeat_runs.py   # Run 1 vs Run 2

# Earlier mixed-version Track 3 / Track 5 run (superseded; requires a Gemini API key)
python3 scripts/experiments/track3_assessment/run_assessment_eval.py
python3 scripts/experiments/track5_trust/run_trust_eval.py

# Regenerate the manuscript (python-docx)
python3 scripts/build/build_docx.py
```

## Citation

If you use this benchmark, please cite the archived release and, where applicable, the constituent
dataset sources listed above:

> Vairamuthu M, Sudhan MB (2026) EvalBench v1: unified multi-task benchmark for educational document
> processing. Dataset. Zenodo (use the version DOI on the Zenodo record).

## License

Code in this repository is released under the MIT License (see `LICENSE`). The processed
manifest (`data/processed/evalbench_v1.jsonl`) is released under CC BY 4.0, subject to the
licensing terms of its constituent source datasets noted above.

## Contact

For questions regarding the benchmark or reproducibility package, please contact:

**Vairamuthu M.**
SRM Institute of Science and Technology
Email: vm8470@srmist.edu.in

or

**Sudhan M. B.**
SRM Institute of Science and Technology
Email: sudhanm@srmist.edu.in
