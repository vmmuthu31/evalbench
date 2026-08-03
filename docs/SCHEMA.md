# EvalBench JSON Schema v2.0

Every record in `data/processed/evalbench_v1.jsonl` follows the schema in `schema/schema.json`.

## Required fields

| Field | Type | Description |
|---|---|---|
| `record_id` | string | Unique identifier, e.g. `MDLY-0001` |
| `dataset` | string | Source dataset, e.g. `mendeley`, `iam`, `iiit_word` |
| `language` | string | e.g. `English` |
| `image_path` | string, nullable | Path to the source image (not redistributed for licensed sources — see main README) |
| `ocr_text` | string, nullable | Ground-truth transcription, used by Track 1 |
| `ground_truth` | string, nullable | Reference answer text, used by Tracks 2-5 where applicable |
| `teacher_score` | number, nullable | Human-assigned score, used by Tracks 3 and 5 |
| `max_score` | number, nullable | Maximum possible score for the item |
| `track` | string | Schema value grouping records by task family (`ocr_substrate`, `scored_answer_core`, `multimodal`) |
| `license` | string | License of the source record, e.g. `CC BY 4.0` |
| `split` | string | `train`, `val`, or `test` |
| `extra` | object, nullable | Track-specific payload not covered by the named fields above (e.g. Track 5's `confidence`, `evidence`, `reasoning`) |

## Splits

Stratified by dataset source using scikit-learn's `StratifiedShuffleSplit` with `random_state=42`,
nominal 70/10/20 train/val/test for larger sources. Mendeley (50 records) is assigned entirely to
test. gopika13 (101 records) is assigned entirely to train. See `docs/TRACKS.md` and the manuscript
Section 3.2 for the full split rationale, including known asymmetries to be aware of before
building on this release.

## Loading the data

See `examples/load_dataset.py` for a minimal loader.
