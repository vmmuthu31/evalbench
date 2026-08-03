# EvalBench Tracks

EvalBench defines five evaluation tracks under one JSON schema (`schema/schema.json`). This pilot
release (v1.0.0-pilot) reports experimental results for Tracks 1, 3, and 5. Tracks 2 and 4 are
fully specified but have no evaluation script or labelled ground truth yet — see the Roadmap
section of the main README.

| Track | Task | Metrics | Datasets | Status in v1.0.0-pilot |
|---|---|---|---|---|
| 1 — OCR | Transcribe handwritten text from an image | CER, WER, Character Accuracy, Exact Match | iam, iiit_word, iiit_page, anshcode1, gopika13 | Reported |
| 2 — Document Understanding | Page structure parsing, answer localization, layout understanding | Answer extraction F1, page structure accuracy | iam, iiit_page, gopika13, ieee | Schema-defined only, no baseline |
| 3 — Educational Assessment | Given a handwritten answer image and (optionally) a rubric, assign a score | Score MAE, Pearson r, Spearman rho, Exact Score Match | mendeley, ieee | Reported |
| 4 — Multimodal Understanding | STEM diagram interpretation, visual reasoning, VQA over educational documents | VQA accuracy, diagram interpretation accuracy | gopika13 | Schema-defined only, no baseline |
| 5 — Trustworthiness | Confidence calibration, evidence generation, explanation quality | ECE, AUROC, Evidence Generation Rate, Reasoning Rate | mendeley, ieee | Reported |

Note: the schema currently labels the Track 5 evidence metric `grounding_score`, but the manuscript
reports it as **Evidence Generation Rate** — a presence check on whether the model produced a
non-empty evidence citation, not a verified-support "grounding" metric in the trustworthy-AI sense.
The schema field name will be aligned to the paper's terminology (`evidence_generation_rate`) in a
future schema revision; until then, treat the two names as synonyms.

See `schema/schema.json` for the authoritative field-level definitions, including the required
record fields (`record_id`, `dataset`, `split`, `image_path`, `ocr_text`/`ground_truth`, `track`)
and the `extra` catch-all used for track-specific fields such as Track 5's `confidence`,
`evidence`, and `reasoning`.
