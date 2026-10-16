"""
Build the EvalBench manuscript as a .docx file with embedded figures.
Run:  python3 evalbench_paper2/paper_draft/build_docx.py
"""

from __future__ import annotations
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

ROOT     = Path(__file__).parent.parent.parent
FIG_DIR  = ROOT / "evalbench_paper2/outputs/figures"
OUT_PATH = ROOT / "evalbench_paper2/paper_draft/EvalBench_Manuscript_Blinded.docx"

doc = Document()

# ── page margins ──────────────────────────────────────────────────────────────
section = doc.sections[0]
section.top_margin    = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin   = Inches(1.2)
section.right_margin  = Inches(1.2)

# ── helpers ───────────────────────────────────────────────────────────────────
def h1(text):
    p = doc.add_heading(text, level=1)
    p.runs[0].font.size = Pt(13)
    p.runs[0].font.color.rgb = RGBColor(0, 0, 0)
    return p

def h2(text):
    p = doc.add_heading(text, level=2)
    p.runs[0].font.size = Pt(11)
    p.runs[0].font.color.rgb = RGBColor(0, 0, 0)
    return p

def body(text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.first_line_indent = Inches(0.3)
    for run in p.runs:
        run.font.size = Pt(11)
    return p

def caption(text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(10)
    for run in p.runs:
        run.font.size = Pt(9)
        run.font.italic = True
    return p

def fig(filename, cap_text, width=5.5):
    path = FIG_DIR / filename
    if path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(path), width=Inches(width))
    else:
        doc.add_paragraph(f"[Figure not found: {filename}]")
    caption(cap_text)

def _set_cell_border(cell, **kwargs):
    """Set individual borders (top/bottom/left/right) on a table cell.
    kwargs values are dicts like {"sz": 8, "val": "single", "color": "000000"}
    or None to explicitly suppress a border (Elsevier style: no vertical rules)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn('w:tcBorders'))
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ("top", "bottom", "left", "right"):
        if edge not in kwargs:
            continue
        tag = f"w:{edge}"
        el = tcBorders.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            tcBorders.append(el)
        spec = kwargs[edge]
        if spec is None:
            el.set(qn('w:val'), 'nil')
        else:
            el.set(qn('w:val'), spec.get("val", "single"))
            el.set(qn('w:sz'), str(spec.get("sz", 8)))
            el.set(qn('w:space'), "0")
            el.set(qn('w:color'), spec.get("color", "000000"))


def add_table(headers, rows, cap_text):
    """Elsevier house style: horizontal rules only (top of header, below header,
    bottom of table) -- no vertical rules, no shading within cells."""
    caption(cap_text)
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    NONE_ = None
    THIN  = {"sz": 6, "val": "single", "color": "000000"}
    THICK = {"sz": 12, "val": "single", "color": "000000"}
    n_rows = 1 + len(rows)
    for ri in range(n_rows):
        for ci in range(len(headers)):
            cell = t.rows[ri].cells[ci]
            top    = THICK if ri == 0 else NONE_
            bottom = THIN if ri == 0 else (THICK if ri == n_rows - 1 else NONE_)
            _set_cell_border(cell, top=top, bottom=bottom, left=NONE_, right=NONE_)
    hrow = t.rows[0]
    for i, h in enumerate(headers):
        cell = hrow.cells[i]
        cell.text = h
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.size = Pt(9)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for ri, row in enumerate(rows):
        drow = t.rows[ri + 1]
        for ci, val in enumerate(row):
            cell = drow.cells[ci]
            cell.text = str(val)
            for run in cell.paragraphs[0].runs:
                run.font.size = Pt(9)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

def ref(authors, year, title, journal, doi=""):
    """Elsevier Harvard-style reference entry: Authors, Year. Title. Journal. DOI/URL."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent       = Inches(0.4)
    p.paragraph_format.first_line_indent = Inches(-0.4)
    p.paragraph_format.space_after       = Pt(4)
    run = p.add_run(f"{authors}, {year}. {title}. {journal}.")
    run.font.size = Pt(10)
    if doi:
        run2 = p.add_run(f" {doi}")
        run2.font.size = Pt(10)

def surname_key(authors):
    """Sort key: lowercased first-author surname for alphabetical Harvard-style ordering."""
    first = authors.split(",")[0].strip()
    return first.lower()

# ══════════════════════════════════════════════════════════════════════════════
#  TITLE  (author block intentionally omitted pending journal submission decision)
# ══════════════════════════════════════════════════════════════════════════════
title_para = doc.add_paragraph()
title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title_para.add_run(
    "EvalBench: A Unified Multi-Task Evaluation Framework for Reliable AI-Based Educational "
    "Document Processing"
)
run.bold = True
run.font.size = Pt(16)
doc.add_paragraph()

# Note: the Graphical Abstract is NOT embedded in the manuscript body. Elsevier's
# submission system (Editorial Manager) takes it as its own separate upload item
# ("Graphical abstract" file type) and it is not typically shown in the article
# PDF at all -- see graphical_abstract.png/.pdf/.tiff, submitted standalone.

# Note: Highlights are NOT embedded in the manuscript body either -- same treatment
# as the Graphical Abstract. Elsevier: "Highlights ... won't (yet) appear in the
# article PDF file or print" -- they're their own separate upload item (see
# EvalBench_Highlights.docx, submitted standalone with 'Highlights' in the filename).

# ══════════════════════════════════════════════════════════════════════════════
#  ABSTRACT  (single paragraph, per Scopus/SCIE journal convention)
# ══════════════════════════════════════════════════════════════════════════════
h1("Abstract")
body(
    "This work's AI contribution is EvalBench v1, a unified multi-task evaluation framework; its "
    "engineering application is educational document-processing infrastructure, where optical "
    "character recognition (OCR), grading, and trustworthiness checks are built and validated "
    "separately, hiding cross-task failures until deployment. EvalBench v1 is a pilot release of "
    "132,891 quality-filtered records from six public datasets, organised into five tracks (OCR, "
    "document understanding, educational assessment, multi-modal understanding, trustworthiness) "
    "under one schema, with a default 70/10/20 split, exceptions for smaller sources, and a "
    "reproducible harness. Four tracks are reported experimentally; the fifth is schema-complete, "
    "held for later release. OCR model rankings prove unstable across datasets: TrOCR-base reaches "
    "the highest Exact Match (EM) on IAM (EM = 0.553) but ranks third on IIIT-Word (EM = 0.291), "
    "while PaddleOCR leads on IIIT-Word (EM = 0.664) yet ranks last on IAM (EM = 0.075) -- a "
    "reversal single-corpus evaluation would not catch. For assessment, Gemini Flash grades 50 "
    "handwritten exam papers with no rubric, reaching a mean absolute error (MAE) of 3.78 marks, "
    "r = 0.543. In the trustworthiness track, the model produced non-empty evidence for 100% of "
    "predictions, but its confidence weakly discriminated correct from incorrect scores (area "
    "under the receiver operating characteristic curve, AUROC = 0.571, 95% CI 0.320-0.680, "
    "crossing chance at 0.5; expected calibration error, ECE = 0.251) -- a pattern accuracy-only "
    "evaluation would miss, though the wide CI at n = 50 keeps this suggestive, not precise. "
    "EvalBench v1, with its scripts and outputs, supports reproducible engineering of educational "
    "AI systems."
)
body(
    "Keywords: Educational AI evaluation; Handwritten text recognition; Automated exam scoring; "
    "Confidence calibration; Multi-task benchmark; Vision-language models"
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1 – INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════
h1("1. Introduction")
body(
    "Artificial intelligence is already active in classrooms, reading handwritten answer sheets, "
    "scoring exam papers, and offering feedback on student work, and a systematic review of "
    "intelligent tutoring systems documents how rapidly this class of deployment has grown over the "
    "past decade (Lin et al., 2023). What has not kept pace with this "
    "adoption is the infrastructure used to evaluate whether these systems actually work as "
    "intended. OCR tools are validated on one corpus, grading tools on another, and trustworthiness "
    "properties such as confidence calibration are rarely measured at all, in terms of any "
    "standard practice. This fragmentation makes it difficult to establish the reliability that "
    "high-stakes educational deployment requires."
)
body(
    "This study was undertaken to address all three gaps within a single engineering evaluation "
    "framework for automated examination-document processing. EvalBench "
    "introduces a five-track evaluation protocol, covering OCR accuracy, document understanding, "
    "educational assessment, multi-modal question answering, and trustworthiness, built on one "
    "shared data schema and one reproducible evaluation harness. As with any pilot release, the "
    "schema defines all five tracks but this paper reports experimental results for four of them; "
    "Section 3 states which, and why. The unified schema still makes it possible to compare "
    "models across tasks and to identify failure modes that single-task evaluation cannot detect, "
    "which is a deployment-relevant distinction, not only an academic one: Section 4.2 shows that a "
    "team validating an OCR component on IAM alone would deploy TrOCR-base, while a team validating "
    "on IIIT-Word alone would deploy PaddleOCR, and Section 4.5 shows that a system passing an "
    "evidence-generation check would still be unsafe to trust for automated review flagging. "
    "EvalBench is built to surface exactly this kind of model-selection and deployment consequence "
    "before it reaches production, rather than after."
)
body(
    "The key contributions of this study are as follows."
)
items = [
    "We propose EvalBench v1, a unified evaluation framework spanning five task tracks under a "
    "common JSON schema and split protocol, released here as a pilot with four tracks "
    "experimentally validated and one schema-complete track planned for a follow-up release. No "
    "existing benchmark identified in our systematic comparison (Section 2, Table 1) provides this "
    "particular combination of cross-corpus OCR, document-level educational assessment, grading, "
    "and trustworthiness evaluation under one reproducible schema, rather than treating each task "
    "as an isolated evaluation problem.",

    "We construct and release a fused benchmark corpus of 132,891 records from six independent, "
    "publicly available datasets spanning handwritten word recognition, full-page exam OCR, graded "
    "assessment papers, and handwritten question answering; the corpus is dominated by word-level "
    "OCR data (123,325 records), while the assessment and trustworthiness tracks draw on the 50 "
    "papers that carry genuine teacher-assigned grades, a distinction we return to throughout.",

    "We provide empirical baselines for five OCR and vision-language models, namely Tesseract 5 "
    "(Smith, 2007), EasyOCR (JaidedAI, 2020), TrOCR-base (Li et al., 2023), PaddleOCR (PaddleOCR Team, 2025), and Florence-2-base (Xiao et al., 2024), together with "
    "Gemini vision-language model variants (Gemini Team, 2023) across four tracks.",

    "We demonstrate a bidirectional rank reversal across OCR datasets, with cross-dataset Exact "
    "Match gaps as large as 0.589, which confirms that single-corpus evaluation produces "
    "systematically misleading model rankings.",

    "We define Track 5 (Trustworthiness), which measures confidence calibration and evidence "
    "generation independently of score accuracy and helps to expose overconfidence that standard "
    "accuracy metrics alone cannot detect.",
]
for item in items:
    p = doc.add_paragraph(item, style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    for run in p.runs:
        run.font.size = Pt(11)

body(
    "It is worth stating this scope explicitly. EvalBench does not introduce a new OCR architecture, "
    "a new grading model, or a new training procedure; every model evaluated in this paper is an "
    "existing, publicly available system. The contribution is evaluation infrastructure, in the "
    "tradition of benchmark papers such as GLUE, OCRBench, and EssayJudge (Section 2). It consists of "
    "a common schema, a default split protocol with documented per-dataset exceptions (Section 3), "
    "and an evaluation harness that together make it "
    "possible to compare models across five previously separate educational-AI task families under "
    "identical conditions. This kind of contribution is judged on reproducibility, coverage, and "
    "whether it surfaces "
    "failure modes single-task evaluation would miss, criteria addressed directly by the rank-reversal "
    "and calibration-decoupling results in Sections 4 to 6, rather than on algorithmic novelty."
)
body(
    "The engineering artifact contributed by this work is not a new recognition or grading model, "
    "but a reproducible verification and validation layer for AI-based examination-document "
    "processing. Its purpose is to support model selection, failure diagnosis, and pre-deployment "
    "acceptance testing across OCR, grading, and confidence-estimation components."
)
fig("fig15_architecture.png",
    "Fig. 1. EvalBench v1 architecture: one unified schema and evaluation harness spanning five "
    "tracks, with per-track source datasets and status in this pilot release.")
body(
    "Fig. 1 gives the full five-track structure at a glance before the paper works through it "
    "section by section. It shows which datasets feed each track, and which of the five are "
    "experimentally complete in this release versus schema-complete and planned for v1.1+."
)
fig("fig17_framework_pipeline.png",
    "Fig. 2. EvalBench v1 evaluation pipeline: from raw source data through quality filtering, "
    "the unified schema, fixed splits, and the evaluation harness, to per-track baselines and the "
    "headline leaderboard.")
body(
    "Where Fig. 1 shows the five-track structure, Fig. 2 shows the processing pipeline that "
    "produces it, the seven stages from raw source data to the headline leaderboard in Table 11. "
    "Every stage is deterministic and re-runnable from the released scripts (Data and Code "
    "Availability): the 224,427 raw records are filtered to 132,891 quality-passing records "
    "(Section 3), mapped onto the unified schema, partitioned by the default 70/10/20 split protocol "
    "(with the dataset-specific exceptions noted in Section 3), "
    "and evaluated through one harness whose OCRModel interface and VLM prompt pipeline are shared "
    "across all five tracks rather than reimplemented per track."
)
body(
    "This study is organised around four research questions, each targeted at one of the failure "
    "modes single-task, single-corpus evaluation cannot surface."
)
research_questions = [
    ("RQ1", "How stable are AI model rankings across heterogeneous handwriting and document "
            "corpora? Addressed in Track 1 (Section 4.2)."),
    ("RQ2", "How accurately can vision-language models perform rubric-free assessment of "
            "handwritten examination papers? Addressed in Track 3 (Section 4.4)."),
    ("RQ3", "Does model-reported confidence reliably discriminate correct from incorrect "
            "assessment decisions? Addressed in Track 5 (Sections 4.5 and 4.6)."),
    ("RQ4", "What failure modes become observable when OCR, assessment, and trustworthiness are "
            "evaluated within a unified framework? Addressed through the integrated analysis in "
            "Sections 5 and 6."),
]
for rq_id, rq_text in research_questions:
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(4)
    run_id = p.add_run(f"{rq_id}: ")
    run_id.font.bold = True
    run_id.font.size = Pt(11)
    run_rest = p.add_run(rq_text)
    run_rest.font.size = Pt(11)
body(
    "The remainder of the paper is organised as follows. Section 2 reviews related work on "
    "handwriting recognition and educational AI. Section 3 describes the EvalBench v1 dataset, "
    "schema, and pre-processing steps. Section 4 reports experimental results across four tracks. "
    "Section 5 presents an ablation study isolating the cross-dataset ranking effect. Section 6 "
    "discusses the findings and their limitations. Section 7 concludes with directions for future "
    "work."
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2 – RELATED WORK
# ══════════════════════════════════════════════════════════════════════════════
h1("2. Related Work")

h2("2.1 Handwritten Text Recognition and OCR")
body(
    "Handwritten text recognition has been a long-standing problem in computer vision and document "
    "processing. Early methods relied on handcrafted features and rule-based pipelines, which meant "
    "researchers had to design recognition rules manually. Convolutional recurrent architectures "
    "later made it possible to train sequence recognition end-to-end without an explicit "
    "segmentation step (Shi et al., 2016), and Transformer-based architectures subsequently changed "
    "this further by learning character patterns directly from image data, which helps to explain "
    "the large accuracy gains reported over the last few years (Crosilla et al., 2025). A recent "
    "survey traces this progression from heuristic pipelines to contemporary neural models in more "
    "detail (Garrido-Munoz et al., 2025)."
)
body(
    "A 2025 benchmarking study compared eight large language models on handwritten text recognition "
    "and found that proprietary systems such as GPT-4o produced lower character error rates than "
    "open-source alternatives across a range of writing styles (Crosilla et al., 2025). PaddleOCR 3.0, released the "
    "same year, restructured its detection-recognition pipeline and reported measurable precision "
    "gains on scene text over earlier versions (PaddleOCR Team, 2025). However, such studies are typically evaluated "
    "on a single corpus, which means cross-dataset generalisation remains largely unreported."
)
body(
    "Layout-aware recognition has also advanced. The PILOT framework was developed to handle "
    "documents with mixed text and table regions, a structure common in exam papers where answers "
    "are interleaved with printed questions (Hamdi et al., 2025), which makes it directly relevant to educational "
    "document evaluation. OCRNet, a hybrid CNN architecture published in 2025, reports 95% accuracy "
    "on alphanumeric character recognition without a large pre-trained backbone (Nagasubramanian et al., 2025). The closest "
    "prior work to EvalBench's Track 1 design is OCRBench (Y. Liu et al., 2024), a 29-dataset OCR evaluation suite "
    "for large multimodal models that already covers handwritten text recognition among other "
    "sub-tasks, however OCRBench evaluates OCR in isolation and does not extend to grading or "
    "trustworthiness, which is exactly the gap EvalBench is built to close. Within the OCR track "
    "specifically, EvalBench addresses the cross-corpus gap directly by evaluating every model on "
    "both IAM and IIIT-Word under one shared metric set, which is precisely what makes the rank "
    "reversal reported in Section 4 visible."
)
body(
    "Document-level understanding has followed a parallel trajectory. LayoutLMv3 pre-trains a "
    "multimodal Transformer with unified text and image masking so that a single model handles both "
    "text-centric and image-centric document tasks (Y. Huang et al., 2022), and Donut removes the "
    "OCR engine from the pipeline entirely, mapping a document image directly to structured text "
    "through an encoder-decoder Transformer (Kim et al., 2022). Both directions inform Track 2's "
    "design choice to evaluate classical OCR and a vision-language baseline side by side on the same "
    "exam-page images, rather than committing to one paradigm in advance."
)

h2("2.2 Automated Exam and Essay Scoring")
body(
    "Automated essay and short-answer scoring predates the current wave of large language models: "
    "an early neural approach trained a convolutional-recurrent network end-to-end on the ASAP "
    "benchmark and reported a Quadratic Weighted Kappa (Cohen, 1960) of 0.708 (Taghipour and Ng, 2016), "
    "establishing the neural, feature-free baseline that later transformer-based systems build on. "
    "Two subsequent surveys track that transition in more detail: Haller et al. (2022) trace "
    "short-answer grading from word embeddings through transformer encoders such as BERT (Devlin "
    "et al., 2019), and Misgna et al. (2024) cover essay "
    "scoring and feedback generation specifically. Studies from 2024 and 2025 "
    "report that LLM-based graders can approach "
    "human agreement, such as reaching a Quadratic Weighted Kappa of 0.68 in one setting (Liew and Tan, 2024), "
    "and open-source LLMs have also been used to both score and revise essays in the same pass "
    "(Song et al., 2024). A cross-disciplinary survey of auto-grading with large language models "
    "reports similarly encouraging results across subjects (Eneye et al., 2025). "
    "However, these models sometimes deviate from the rubric they were given, which means their "
    "scores can drift from what a human grader would assign."
)
body(
    "EssayJudge, introduced in 2025, is a multi-granular benchmark that was developed to test "
    "vision-language models on trait-specific essay scoring across several dimensions rather than a "
    "single overall grade (Su et al., 2025). It appears to be the first benchmark placing proprietary systems such "
    "as GPT-4o and Gemini-1.5-Pro alongside open-source models on grading consistency specifically. "
    "A related study evaluating vision-language models in Indonesian classrooms found that these "
    "systems identify fully correct answers reliably but handle partial credit poorly (Aisyah et al., 2025), a "
    "pattern that recurs in Section 4.4."
)
body(
    "A 2026 study on automated exam grading with foundation models examined fairness-aware "
    "recognition of handwritten answers, achieving 98.4% recognition accuracy on a benchmark of 61 "
    "anonymised exams (Grabowski, 2026), which helps to make the point that grading benchmarks built purely around "
    "correlation with a human score remain incomplete. Evaluation frameworks for educational AI "
    "therefore need to look beyond aggregate accuracy toward the properties that determine whether a "
    "system is safe to deploy, which is the motivation behind EvalBench's dedicated trustworthiness "
    "track."
)
body(
    "Concurrently with this work, a large-scale study of OCR-conditioned LLM grading on handwritten "
    "college calculus proposes a standardised benchmark for AI grading of handwritten mathematics, "
    "built from thousands of real student submissions and validated against teaching-assistant "
    "scores (Yu et al., 2026). That effort and EvalBench are complementary rather than overlapping: it goes deep "
    "on a single domain (handwritten calculus, partial-credit grading, TA-aligned rubric design), "
    "whereas EvalBench stays domain-general and adds the calibration and evidence-generation checks "
    "that a grading-only benchmark does not cover. The appearance of both efforts in the same period "
    "is itself evidence that OCR-conditioned grading evaluation is a gap the field is actively "
    "converging on, not a niche concern."
)

h2("2.3 Confidence Calibration and Trustworthiness in AI")
body(
    "Calibration concerns whether a model's stated confidence matches its empirical accuracy, and it "
    "is one part of the broader uncertainty-estimation literature that separates data uncertainty "
    "from model uncertainty and surveys the methods proposed to quantify each (Gawlikowski et al., 2023). A "
    "2025 survey of uncertainty quantification in large language models concludes that most "
    "instruction-tuned models are systematically overconfident (X. Liu et al., 2025), which is a serious concern in "
    "any setting where a wrong but confident answer causes real harm, exam grading being an obvious "
    "example, and a related survey traces this same overconfidence back to the broader problem of "
    "hallucination in large language models (L. Huang et al., 2023). Guo et al. (2017) demonstrated this overconfidence problem in standard deep networks and "
    "proposed temperature scaling as a low-cost post-hoc correction that reduces Expected "
    "Calibration Error without altering the underlying model."
)
body(
    "Closer to the present setting, a study on confidence estimation for automatic short "
    "answer grading found that LLMs readily produce a confidence value, but that value does not "
    "reliably track whether the underlying answer is correct (Cong et al., 2026). A companion 2024 survey reviewed "
    "post-hoc calibration techniques for black-box LLMs and found no single method that generalises "
    "across task types (Xie et al., 2024). A 2026 study evaluating self-reported confidence, self-consistency "
    "voting, and token probability across seven LLMs on three educational grading datasets reports "
    "an average ECE of 0.166 for the best-performing method (Ferrer et al., 2026), a finding broadly consistent with "
    "the overconfidence pattern reported in Track 5, though that study measures calibration on "
    "typed short-answer grading rather than handwritten exam scoring with evidence generation. This "
    "body of work helps to justify the design of Track 5, in that it measures calibration, evidence "
    "generation, and reasoning as three separate, independently interpretable properties rather than "
    "one combined score."
)

h2("2.4 Multi-Task and Vision-Language Benchmarks")
body(
    "Multi-task benchmarking has an established record in NLP research. GLUE (Wang et al., 2018) and SuperGLUE "
    "(Wang et al., 2019) aggregated diverse sentence-level tasks into a single leaderboard score, which made it "
    "possible to compare models on general language competence rather than isolated task "
    "performance, MMLU pushed the same idea toward broad world knowledge across 57 subjects "
    "(Hendrycks et al., 2020), and BIG-Bench later extended this to 204 distinct tasks contributed "
    "by hundreds of authors (Srivastava et al., 2023). HELM took a complementary approach, taxonomising "
    "scenarios and metrics (including calibration) into one living, continuously updated evaluation "
    "rather than a fixed leaderboard (Liang et al., 2022), which is closer in spirit to EvalBench's own "
    "multi-metric, multi-track design than a single-score benchmark is. The underlying Transformer "
    "architecture that all of these language models share was itself only introduced in 2017 (Vaswani "
    "et al., 2017), and general-purpose multimodal systems built on it, including GPT-4's vision "
    "variant (OpenAI, 2023), LLaVA (H. Liu et al., 2023), Qwen-VL (Bai et al., 2023), and InternVL "
    "(Chen et al., 2024), are exactly the class of model EvalBench's Track 2 and Track 3 baselines "
    "draw on. Vision-language research "
    "has followed a similar path toward broader, more systematic benchmarking. PM4Bench, released in 2025, evaluates large vision-language "
    "models across a parallel multilingual, multi-modal corpus spanning ten languages (Gao et al., 2025), and "
    "LENS adopts an open-set configuration in which models answer natural-language queries grounded "
    "in photographic content (Yao et al., 2025), both useful steps toward more realistic evaluation conditions."
)
body(
    "None of these frameworks, however, were designed with education in mind. Their tasks are drawn "
    "from general-domain photography, web text, or captioning corpora, none of which resemble a "
    "handwritten exam script or a teacher's rubric. EvalBench occupies the space these benchmarks "
    "leave open, in that it borrows the shared-schema, multi-track structure that GLUE-style "
    "benchmarks popularised, but applies it to the document types and grading tasks specific to "
    "education, namely handwriting recognition, rubric-free scoring, and confidence calibration "
    "under a grading workload, evaluated together rather than in isolation."
)

h2("2.5 Positioning Relative to Existing Benchmarks")
body(
    "Table 1 summarises how "
    "EvalBench relates to the closest prior benchmarks discussed above on eight axes: publication "
    "year, whether the benchmark evaluates OCR, whether it evaluates grading, whether it evaluates "
    "trustworthiness or calibration, whether it defines a single unified schema spanning multiple "
    "task types, whether it is built around educational documents specifically rather than "
    "general-domain text or images, whether the benchmark's data is publicly available, and, "
    "separately, whether its evaluation scripts are publicly released rather than only its results "
    "or a static leaderboard. Splitting data and scripts into two columns matters because a public "
    "dataset without a runnable evaluation harness still leaves independent reproduction of the "
    "reported numbers to each user's own re-implementation. The comparison is drawn from each "
    "benchmark's own published description and code/data availability at the time of writing rather "
    "than from re-running it, since the point being illustrated is coverage of capability, not "
    "head-to-head performance."
)
add_table(
    headers=["Benchmark", "Year", "OCR", "Grading", "Trustworthiness", "Unified Schema",
             "Educational Focus", "Public Data", "Eval Scripts Released"],
    rows=[
        ["OCRBench (Y. Liu et al., 2024)",        "2024",    "Yes", "No",  "No",  "No",  "No",  "Yes", "Yes"],
        ["EssayJudge (Su et al., 2025)",       "2025",    "No",  "Yes", "No",  "No",  "Yes", "Not confirmed", "Not confirmed"],
        ["GLUE / SuperGLUE",     "2018-19", "No",  "No",  "No",  "Yes", "No",  "Yes", "Yes"],
        ["PM4Bench (Gao et al., 2025)",        "2025",    "No",  "No",  "No",  "No",  "No",  "Yes", "Not confirmed"],
        ["EvalBench v1 (ours)",  "2026",    "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"],
    ],
    cap_text="Table 1. Quantitative and qualitative comparison between EvalBench v1 and the closest "
             "prior benchmarks, based on each benchmark's published description and public code/data "
             "availability at the time of writing. 'Eval Scripts Released' is judged separately from "
             "'Public Data' since a released dataset does not by itself guarantee a runnable, "
             "reproducible evaluation pipeline."
)
body(
    "No row besides EvalBench has a Yes in more than two of the five capability columns. OCRBench is "
    "the strongest prior OCR benchmark but stops at OCR, though it does release its own evaluation "
    "tooling; EssayJudge is the strongest prior grading benchmark but does not evaluate OCR or "
    "calibration at all, and neither its data release nor a runnable evaluation script could be "
    "confirmed as of this writing; GLUE and SuperGLUE popularised the unified-schema, multi-task "
    "leaderboard format this paper borrows, but for general-domain sentence tasks rather than "
    "education; and PM4Bench extends multi-task vision-language evaluation to new languages without "
    "touching grading, trustworthiness, or educational documents, and its evaluation scripts could "
    "not be confirmed as separately released from its data. EvalBench is the only entry in the table "
    "that combines all five capability columns while also releasing both its processed corpus and "
    "its full, runnable evaluation scripts publicly (see Data and Code Availability), which is the "
    "concrete, tabulated version of the novelty claim made in Section 1."
)

h2("2.6 Why Existing Benchmarks Are Insufficient")
body(
    "Table 1 shows the gap; this subsection explains why it cannot be closed by simply running an "
    "existing benchmark on educational data, or by combining two existing benchmarks side by side."
)
body(
    "OCRBench cannot evaluate grading because it has no notion of a graded outcome in its schema: "
    "its 29 constituent datasets carry ground-truth transcriptions, not teacher-assigned scores, "
    "confidence judgements, or evidence citations, so extending it to Track 3 or Track 5 would "
    "require building an entirely new annotation layer rather than adjusting an evaluation script. "
    "EssayJudge cannot evaluate OCR because its inputs are already-legible essay text and trait "
    "rubrics; it was not designed to test whether a system can first read a handwritten page "
    "correctly before grading it, so a model that fails at transcription but happens to guess a "
    "plausible score would be invisible to it. GLUE and SuperGLUE cannot evaluate educational "
    "documents because their constituent tasks, natural language inference, sentiment classification, "
    "coreference resolution and similar, are built from general-domain sentence pairs with no "
    "handwriting, no exam layout, and no grading rubric anywhere in the pipeline; adapting them would "
    "mean discarding the tasks rather than reusing them."
)
body(
    "Concatenating OCRBench and EssayJudge results side by side, the most obvious workaround, would "
    "still not produce what EvalBench provides, because the two benchmarks use different corpora, "
    "different splits, and different metric conventions, so there is no shared record linking an OCR "
    "failure on a specific handwritten answer to the grading error it causes downstream. EvalBench's "
    "single schema, with every record carrying a record_id, dataset, split, track, and track-specific "
    "fields under one JSON Schema (Section 3.1), is what makes that link possible: the same "
    "underlying document can, in principle, be traced through OCR, grading, and trustworthiness "
    "evaluation without switching corpora or metric definitions partway through. That cross-task "
    "traceability, not any single track in isolation, is what existing benchmarks do not provide and "
    "what this paper contributes."
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3 – DATASET
# ══════════════════════════════════════════════════════════════════════════════
h1("3. Dataset Description and Pre-processing")
body(
    "No single publicly available dataset covers all five tracks EvalBench is designed to evaluate, "
    "so the corpus was assembled from six independent sources rather than one. Together these "
    "sources contribute 132,891 records spanning word-level handwriting crops, full examination "
    "page scans, teacher-graded exam PDFs, and handwritten question-answer pairs, a composition "
    "chosen to stress different aspects of document understanding rather than to maximise record "
    "count alone."
)

body(
    "In the Tracks column of Table 2, the numbers refer to the five evaluation tracks defined in "
    "Section 1: 1 is OCR accuracy, 2 is document understanding, 3 is educational assessment, 4 is "
    "multi-modal question answering, and 5 is trustworthiness."
)
add_table(
    headers=["Dataset", "Type", "Total", "Train", "Val", "Test", "Tracks"],
    rows=[
        ["IAM (Marti and Bunke, 2002)",           "Word (handwritten)",       "38,305",  "26,813", "3,831", "7,661",  "1"],
        ["IIIT English Word (Mishra et al., 2012)", "Word (handwritten)",   "85,020",  "59,513", "8,503", "17,004", "1"],
        ["IIIT English Page",  "Page (exam)",              "3,500",   "2,450",  "350",   "700",    "1, 2"],
        ["anshcode1",          "Exam script (unlabelled)", "5,915",   "--",     "--",    "5,915",  "1, 2"],
        ["Mendeley (Dinesh, 2026)",      "Exam paper (graded)",      "50",      "--",     "--",    "50",     "3, 5"],
        ["gopika13",           "Word (handwritten)",       "101",     "101",    "--",    "--",     "1, 2, 4"],
        ["Total",              "",                         "132,891", "88,877", "12,684","31,330", ""],
    ],
    cap_text="Table 2. EvalBench v1 dataset composition across six sources, verified against the "
             "processed corpus (datasets/processed/evalbench_v1.jsonl)."
)

body(
    "The split protocol is a default 70/10/20 train/validation/test partition, applied per dataset "
    "so that a model never sees test-split images from any source during training, with three "
    "explicit, dataset-specific exceptions visible in Table 2's Train/Val/Test columns. Mendeley's 50 "
    "graded papers are placed entirely in the test split, since a graded-assessment set this small "
    "cannot usefully support a held-out training partition and every paper is needed for evaluation. "
    "gopika13's 101 records are placed entirely in the train split, reflecting its current role as "
    "unlabelled handwriting-sample material for a future Track 4 baseline rather than as an "
    "evaluation source in this release. anshcode1's 5,915 records are held out entirely as test-split "
    "material pending annotation, as noted below, rather than split by the default ratio. Datasets "
    "without a stated exception, IAM, IIIT English Word, and IIIT English Page, follow the default "
    "70/10/20 ratio directly."
)

body(
    "IIIT English Word (Mishra et al., 2012) is the largest single source once the corpus is verified against the "
    "processed data files: 85,020 word-level records extracted from real examination papers rather "
    "than newspaper-style prose, which introduces a domain shift relative to IAM and is precisely "
    "the property that makes cross-dataset comparison worthwhile. IAM contributes 38,305 processed "
    "word images from 657 different writers, covering offline English handwriting collected outside "
    "any examination context; this is smaller than IAM's full 85,756-image release because the "
    "processing pipeline currently retains only the subset with usable transcriptions and image "
    "quality above the harness's minimum threshold. These are greyscale word crops of variable "
    "width, and the variety of writing styles they contain is what makes them a demanding "
    "character-level recognition test."
)
body(
    "IIIT English Page contributes 3,500 full examination page images at a mean resolution of "
    "2,847 by 3,807 pixels, each paired with transcribed ground-truth text. Page-level scans are a "
    "different kind of test, in that they carry layout structure, line segmentation, and "
    "multi-paragraph flow that a cropped word image cannot represent; this labelled subset is what "
    "supports the Track 2 baseline reported in Section 4.3. anshcode1 contributes a further 5,915 "
    "exam-script page images (CC BY 4.0) that are currently unlabelled, no transcription or "
    "ground-truth score has yet been attached to them, so they are held out as test-split material "
    "pending annotation rather than used in any experiment reported in Section 4. Track 4 "
    "(multi-modal understanding) is specified in the EvalBench schema against gopika13, plus a "
    "second source, the IEEE Answer Sheet Dataset, that is referenced in the schema but has not yet "
    "been downloaded into this release; gopika13 itself supplies handwriting-sample images without "
    "the paired question-answer annotations Track 4 requires, so no baseline is reported for Track 4 "
    "here, and this is a labelled-data gap rather than only a missing baseline, a distinction "
    "discussed further in Section 6.3."
)
body(
    "The Mendeley Graded Exam Papers dataset is the smallest labelled source by record count, "
    "comprising 50 scanned handwritten exam papers, but it is the only source that carries genuine "
    "teacher-assigned scores, ranging from 13 to 43 marks (mean 27.9, standard deviation 7.2). That "
    "scarcity of graded ground truth is precisely why it anchors Tracks 3 and 5, since without it "
    "there would be no way to check whether a predicted score, or the confidence stated in that "
    "score, corresponds to anything a human grader would recognise. gopika13 rounds out the corpus "
    "with 101 supplementary handwriting samples, assigned entirely to the training split rather "
    "than the test split, used to broaden Track 1 coverage beyond IAM and "
    "IIIT-Word."
)

body(
    "Before turning to the rank-reversal result itself, it is worth quantifying how different IAM "
    "and IIIT-Word actually are at the level a model experiences them, namely the joint distribution "
    "of per-record OCR outcomes rather than raw pixel content. For every (model, record) prediction "
    "in the OCR experiment (n = 1,100 per corpus, pooled across all four models), we build a "
    "seven-dimensional feature vector of CER, WER, exact match, character accuracy, normalised "
    "reference length, normalised prediction length, and normalised latency, standardised to zero "
    "mean and unit variance across the pooled sample. The Frechet distance between the resulting "
    "IAM and IIIT-Word feature distributions, the same mean-and-covariance formulation used for FID "
    "in image generation (Heusel et al., 2017), is 0.866; the simpler Euclidean distance between the two class centroids "
    "is 0.597, and a label-permutation test on that centroid distance (2,000 permutations, seed 42) "
    "gives p = 0.0005. This confirms quantitatively, not just visually, that the two corpora induce "
    "measurably different OCR outcome distributions, consistent with the rank reversal reported in "
    "Section 4.2."
)
fig("fig05_tsne_features.png",
    "Fig. 3. PCA projection of the same standardised OCR-outcome feature space (Frechet distance "
    "0.866, centroid-distance permutation p = 0.0005), shown as a two-dimensional visual summary of "
    "the quantitative result above.")
body(
    "Fig. 3 is a two-dimensional PCA projection of that same feature space, included as a visual "
    "summary rather than as the primary evidence. It shows substantial overlap in the dense central "
    "cluster, but also a visibly separate secondary cluster and a long tail of points where the two "
    "datasets diverge, a pattern consistent with the Frechet distance reported above: related enough "
    "to invite direct comparison, yet different enough that a model tuned to one distribution does "
    "not automatically transfer to the other."
)

h2("3.1 Data Schema")
body(
    "Every record, regardless of its originating dataset, is normalised to EvalBench JSON Schema "
    "v2.0 before any track-specific processing begins, which is what allows a single evaluation "
    "harness to run unmodified across six otherwise incompatible data formats. The required fields "
    "are record_id, dataset, split, image_path, ref (the ground-truth text or numeric score), and "
    "track. Track-specific extensions, such as teacher_score and max_score for Tracks 3 and 5, are "
    "included as named optional fields, and a catch-all extra object carries any remaining "
    "track-specific payload (for example the confidence, evidence, and reasoning fields Track 5 "
    "reads for calibration analysis), which keeps each evaluation script self-contained."
)

h2("3.2 Train, Validation, and Test Splits")
body(
    "The corpus is partitioned into training, validation, and test subsets using stratified "
    "sampling by dataset source, so that each subset preserves the proportional representation of "
    "all six sources. Splitting uses scikit-learn's StratifiedShuffleSplit with random_state = 42, "
    "which guarantees an identical split regardless of machine or Python version (>= 3.8). Mendeley "
    "is small enough that every one of its 50 records is assigned directly to the test subset, "
    "while gopika13, at 101 records, is assigned entirely to the training split rather than test, "
    "since its role in this release is to broaden Track 1 training coverage rather than to "
    "contribute held-out evaluation samples. All results reported in this paper are computed "
    "exclusively on the test split of the dataset that produced them."
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4 – EXPERIMENTS
# ══════════════════════════════════════════════════════════════════════════════
h1("4. Experimental Phase")

body(
    "Table 3 gives an at-a-glance map of the full five-track design before the per-track results "
    "below: each track's goal, its source datasets and their combined record count (Total column, "
    "Table 2), the baseline models evaluated against it in this release, the metrics reported, and "
    "status. Track 4 is included for completeness, marked not yet experiment-ready per the "
    "scope discussion in Section 6.3, rather than omitted."
)
add_table(
    headers=["Track", "Goal", "Datasets", "# Records", "Baseline Models (v1)", "Metrics", "Status"],
    rows=[
        ["1. OCR Accuracy",
         "Handwriting recognition",
         "IAM, IIIT English Word",
         "123,325",
         "Tesseract 5, EasyOCR, TrOCR-base, PaddleOCR",
         "CER, WER, Exact Match, Character Accuracy",
         "Complete"],
        ["2. Document Understanding",
         "Layout-aware document reading",
         "IIIT English Page, anshcode1, gopika13",
         "9,516",
         "Tesseract 5, Florence-2-base",
         "CER, WER, Exact Match, Character Accuracy",
         "Complete (preliminary)"],
        ["3. Educational Assessment",
         "Rubric-free exam grading",
         "Mendeley",
         "50",
         "Gemini Flash",
         "MAE, Pearson r, Spearman rho, Exact Match (+/-1)",
         "Complete"],
        ["4. Multi-Modal Understanding",
         "Handwritten question answering",
         "gopika13",
         "101",
         "Not yet implemented",
         "Planned for v1.1+",
         "Schema-complete"],
        ["5. Trustworthiness",
         "Calibration and evidence quality",
         "Mendeley",
         "50",
         "Gemini Flash",
         "ECE, AUROC, Evidence Generation Rate, Reasoning Rate",
         "Complete"],
    ],
    cap_text="Table 3. EvalBench v1 track-by-track summary: goal, source datasets, total available "
             "records (Table 2), baseline models, metrics, and status. Record counts are dataset "
             "totals, not the filtered test-split subsets actually scored in Section 4; see Section "
             "4.2 for exact per-model test sample sizes."
)

h2("4.1 Experimental Setup")
body(
    "All OCR experiments were run on an Apple M3 machine using CPU/MPS only, with no dedicated GPU "
    "involved at any stage, which helps to keep the Track 1 results reproducible on ordinary "
    "hardware. Track 3 and Track 5 experiments instead call the Gemini Flash family of "
    "vision-language models (Gemini Team, 2023) through Google's free-tier API, which imposes its own constraints: rate "
    "limits were handled with exponential backoff (30-120 seconds between retries) and a --resume "
    "flag that skips records already scored. Every evaluation script is a standalone Python 3.10+ "
    "module with a command-line interface and JSONL output, which makes incremental re-runs "
    "straightforward."
)
body(
    "Table 4 lists every system this pilot release's evaluation harness supports, not only the "
    "systems reported below, since the difference between \"integrated\" and \"reported with results\" "
    "matters for a benchmark paper specifically. Tesseract 5, EasyOCR, TrOCR-base, and PaddleOCR are "
    "the four local OCR models with results reported for Track 1 in Section 4.2, and the same "
    "Tesseract 5 plus Florence-2-base are reported for Track 2 in Section 4.3, reusing the identical "
    "OCRModel interface across tracks. Three free hosted OCR APIs (OCR.space, Optiic, API Ninjas) and "
    "one further open vision-language model (Qwen2.5-VL) are already wired into the same evaluation "
    "harness, so extending either track's leaderboard to them is a configuration change, not new "
    "engineering; they are not yet reported here because their free-tier request quotas or compute "
    "footprint make a full test-split run a v1.1 exercise rather than something completed for this "
    "pilot. Gemini is reported for Track 3 and Track 5 as described above."
)
add_table(
    headers=["Model", "Type", "Open", "Free", "Offline", "Track(s)", "Status (v1)"],
    rows=[
        ["Tesseract 5",   "Classical OCR",       "Yes", "Yes", "Yes", "OCR",            "Reported"],
        ["EasyOCR",       "Deep-learning OCR",   "Yes", "Yes", "Yes", "OCR",            "Reported"],
        ["TrOCR-base",    "Transformer OCR",     "Yes", "Yes", "Yes", "OCR",            "Reported"],
        ["PaddleOCR (PaddleOCR Team, 2025)", "Deep-learning OCR",   "Yes", "Yes", "Yes", "OCR",            "Reported"],
        ["OCR.space",     "Hosted OCR API",      "No",  "Yes", "No",  "OCR",            "Integrated, v1.1"],
        ["Optiic",        "Hosted OCR API",      "No",  "Yes", "No",  "OCR",            "Integrated, v1.1"],
        ["API Ninjas",    "Hosted OCR API",      "No",  "Yes", "No",  "OCR",            "Integrated, v1.1"],
        ["Florence-2",    "Vision-language model","Yes","Yes", "Yes", "Document Understanding, OCR", "Reported (Track 2)"],
        ["Qwen2.5-VL",    "Vision-language model","Yes","Yes", "Yes", "OCR",            "Integrated, v1.1"],
        ["Gemini Flash",  "Proprietary VLM",     "No",  "Yes", "No",  "Grading, Trust", "Reported"],
    ],
    cap_text="Table 4. Systems supported by the EvalBench v1 evaluation harness, by track and by "
             "whether results are reported in this pilot release. \"Free\" reflects whether a "
             "no-cost tier is available (with request-volume limits for hosted APIs), not whether "
             "the system is open-source; \"Open\" specifically denotes open-source/open-weight "
             "availability."
)

h2("4.2 Track 1 - OCR Accuracy")
body(
    "Table 5 reports word-level OCR accuracy for four models on the test splits of IAM and IIIT "
    "English Word. Every result is restricted to words of at least three characters, which removes "
    "punctuation-only tokens that would otherwise inflate error rates; after this filter, n = 199 "
    "for IAM and n = 223 for IIIT English Word for three of the four models, and n = 133 and "
    "n = 146 respectively for PaddleOCR. Tesseract 5, EasyOCR, and TrOCR-base were evaluated in one "
    "batch run over 300 raw records per corpus, while PaddleOCR was added in a later, separate run "
    "capped at 200 raw records per corpus; after the reference-length filter this leaves PaddleOCR "
    "with roughly a third fewer samples than the other three models. This is an operational "
    "inconsistency in how this pilot release's evaluation batches were configured rather than a "
    "deliberate design choice, and re-running PaddleOCR at the same sample cap as the other three "
    "models is planned for the next release; the PaddleOCR figures below should be read with that "
    "smaller, non-matched sample size in mind. Four complementary metrics are reported, namely "
    "Character Error Rate (CER), Word Error Rate (WER), Exact Match (EM), and Character Accuracy, "
    "computed as 1 minus CER under a substitution-only edit-distance convention, because no single "
    "metric captures both character-level precision and full-word correctness on its own."
)

add_table(
    headers=["Model", "IAM CER", "IAM EM", "IAM Rank", "IAM CharAcc",
             "IIIT-W CER", "IIIT-W EM", "IIIT-W Rank", "IIIT-W CharAcc"],
    rows=[
        ["Tesseract 5",  "0.798", "0.045", "3", "0.202", "0.662", "0.148", "4", "0.338"],
        ["EasyOCR",      "0.631", "0.045", "2", "0.369", "0.372", "0.296", "2", "0.628"],
        ["TrOCR-base",   "0.229", "0.553", "1", "0.771", "0.522", "0.291", "3", "0.478"],
        ["PaddleOCR (PaddleOCR Team, 2025)","0.513", "0.075", "4", "0.487", "0.177", "0.664", "1", "0.823"],
    ],
    cap_text="Table 5. Word-level OCR results on IAM and IIIT English Word test splits. Rank "
             "columns (1 = best by Exact Match) make the reversal visible directly alongside the "
             "raw metrics; see Table 6 and Fig. 11 for the reversal isolated and tested for "
             "significance."
)

body(
    "The pattern in Table 5 is not subtle, and the Rank columns make it immediate: three of the "
    "four models swap positions entirely between corpora. TrOCR-base posts the best Exact Match on IAM (0.553), "
    "which is consistent with its IAM-adjacent pre-training, but that same model's EM falls to "
    "0.291 on IIIT-Word, a drop of 0.261. PaddleOCR runs the opposite course, reaching 0.664 EM on "
    "IIIT-Word, the best score in the table, against only 0.075 on IAM, a fall of 0.589 in the "
    "other direction. The practical consequence is that whichever model tops the leaderboard on one "
    "dataset is not merely weaker but last-place on the other, which means a team validating only on "
    "IAM and a team validating only on IIIT-Word would reach recommendations that directly "
    "contradict each other."
)
body(
    "To check that these EM gaps are not an artefact of sampling noise, each was tested with an "
    "independent-samples bootstrap (Efron and Tibshirani, 1994; 10,000 resamples, seed 42) and an "
    "independent-samples permutation test over the per-record exact-match indicators; IAM and "
    "IIIT-Word contain different images and are not matched record-for-record, so the gap between "
    "them is a difference between two independent samples rather than a paired comparison, and both "
    "tests are constructed accordingly. Exact intervals and p-values are reported alongside each "
    "model's gap in Table 6 below. All four gaps are statistically significant, none of the four "
    "confidence intervals cross zero, which supports reading the rank reversal as a structural "
    "property of how these models generalise across handwriting styles rather than as noise from a "
    "small test split."
)

fig("fig02_5fold_boxplot.png",
    "Fig. 4. CER distribution across 5 resampled subsets, by model and dataset.")
fig("fig03_confusion_matrix.png",
    "Fig. 5. Character-level confusion matrix for TrOCR-base on IAM (top-10 confused characters).")
fig("fig08_cer_violin.png",
    "Fig. 6. CER distribution violin plot by model and dataset.")

body(
    "Fig. 4 places the CER distributions across 5 resampled subsets for all four models side by "
    "side. TrOCR-base shows the tightest, most stable spread on IAM, consistent with the dataset it "
    "was effectively tuned toward, but that stability does not carry over to IIIT-Word, where its "
    "spread widens noticeably. Fig. 5 isolates where TrOCR-base goes wrong on IAM: the confusion "
    "matrix is dominated by visually similar character pairs such as 'i' and 'l', which suggests "
    "the residual errors are largely perceptual rather than a sign of a broken model. Fig. 6's "
    "violin plot places all four models and both datasets on one axis, and the long lower tails for "
    "TrOCR-base on IIIT-Word and for PaddleOCR on IAM offer the clearest single summary of the "
    "rank-reversal result reported above."
)

add_table(
    headers=["Model", "IAM EM", "IIIT-W EM", "Gap (EM)", "95% CI (gap)", "p-value"],
    rows=[
        ["Tesseract 5", "0.045", "0.148", "-0.103", "[-0.159, -0.047]", "0.0005"],
        ["EasyOCR",    "0.045", "0.296", "-0.251", "[-0.316, -0.184]", "< 0.001"],
        ["TrOCR-base", "0.553", "0.291", "+0.261", "[+0.170, +0.351]", "< 0.001"],
        ["PaddleOCR",  "0.075", "0.664", "-0.589", "[-0.675, -0.497]", "< 0.001"],
    ],
    cap_text="Table 6. Cross-dataset generalisation gap (IAM EM minus IIIT-Word EM), with "
             "independent-samples bootstrap 95% confidence intervals (10,000 resamples, seed 42) and "
             "independent-samples permutation test p-values on the per-record exact-match indicators; "
             "IAM and IIIT-Word are different, unmatched records, so the gap is treated as a "
             "difference between two independent samples."
)

body(
    "Table 6 makes the size of the gap explicit, and significant, rather than leaving it implicit "
    "across two single-dataset tables. TrOCR-base carries the largest positive gap (+0.261), meaning "
    "it performs far better on IAM than on IIIT-Word; PaddleOCR carries the largest negative gap "
    "(-0.589), meaning the reverse. A gap this size is larger than the entire EM score achieved by "
    "three of the four models on IAM, which suggests a structural property of how each architecture "
    "responds to the two corpora rather than ordinary evaluation noise. All four gaps are "
    "statistically significant at p < 0.001, with the sole exception of Tesseract 5 at p = 0.0005, "
    "and none of the four 95% confidence intervals cross zero."
)

h2("4.3 Track 2 - Document Understanding (Preliminary)")
body(
    "This subsection is explicitly a preliminary document-understanding evaluation rather than a "
    "track at the same maturity level as Track 1: two baselines, one labelled source, and n = 50 "
    "records are enough to demonstrate the evaluation harness and surface a striking early finding, "
    "but not enough to support a general claim about page-level OCR performance. Track 2 evaluates page-level OCR on IIIT English Page, the one Track 2 source that carries "
    "both scanned images and transcribed ground-truth text; anshcode1 and gopika13 remain held out "
    "as noted in Section 3. This release reports two baselines over the identical first n = 50 "
    "test-split records, using the same CER/WER/EM/Character-Accuracy metric suite as Track 1, "
    "computed here for the first time at the page rather than the word level: Tesseract 5 "
    "(page-segmentation mode psm=6, 'assume a single uniform block of text'), a classical, "
    "non-handwriting-specialised engine, and Florence-2-base, an open vision-language model already "
    "integrated into the harness for Track 1 (Table 4) and run here with its native <OCR> task "
    "prompt, loaded through the HuggingFace Transformers library (Wolf et al., 2020) on top of "
    "PyTorch (Paszke et al., 2019). Unlike Track 1's cropped word images, these are full examination pages carrying "
    "cursive, multi-line handwriting."
)
add_table(
    headers=["Model", "n", "CER (95% CI)", "WER", "Exact Match", "Character Accuracy (95% CI)"],
    rows=[
        ["Tesseract 5", "50", "6.044 [3.681, 8.740]", "11.489", "0.000",
         "-5.044 [-7.708, -2.665]"],
        ["Florence-2-base", "50", "0.180 [0.149, 0.220]", "0.580", "0.000",
         "0.820 [0.782, 0.852]"],
    ],
    cap_text="Table 7. Track 2 document understanding (page-level OCR) results on IIIT English Page "
             "test split (n=50), with paired bootstrap 95% confidence intervals (10,000 resamples, "
             "seed 42) on CER and Character Accuracy. Both models were evaluated on the identical "
             "50 records for direct comparability."
)
body(
    "Tesseract's headline numbers look broken at first glance, a mean CER above 600% and a negative "
    "Character Accuracy, but they are not a computation error: inspecting individual predictions "
    "shows Tesseract producing long runs of near-random character sequences on genuinely cursive "
    "page images (for example, predicting strings such as 'ae -- er. * Ss | e Wire 4. Vr OAR AS...' "
    "against a coherent reference sentence), with predicted transcripts sometimes running thousands "
    "of characters longer than the corresponding reference. Under an edit-distance-normalised metric, "
    "that volume of spurious insertions pushes CER well past 1.0 and drags Character Accuracy, "
    "defined as 1 minus CER, correspondingly negative. Exact Match is 0.000 across all 50 records, "
    "consistent with a general-purpose OCR engine failing outright on page-level cursive handwriting "
    "rather than merely underperforming."
)
body(
    "Florence-2-base tells a materially different story on the same 50 pages: CER of 0.180 and "
    "Character Accuracy of 0.820, roughly on par with Track 1's word-level results for the stronger "
    "models in Table 5. Inspecting Florence-2's predictions shows mostly-legible, word-segmented "
    "transcriptions with the occasional character-level slip (for example, predicting 'guitarrides' "
    "for 'Guitarridae' and 'Espiipsidae' for 'Esperiopsidae'), the kind of error a spell-checker "
    "would catch, not the wholesale breakdown seen in Tesseract's output. Exact Match remains 0.000 "
    "for both models, since even a single character error anywhere in a full page of running text is "
    "enough to fail a whole-page exact-match criterion, which suggests EM is the wrong headline "
    "metric for page-level Track 2 evaluation even though it is informative at Track 1's word level."
)
body(
    "Taken together, the two baselines are the finding, not a table of numbers to skim past: they "
    "show that word-level OCR accuracy, the metric most commonly used to characterise a model, does "
    "not transfer to page-level document understanding, and that the gap is not a property of "
    "handwritten pages in general but of the specific engine applied to them. A classical, "
    "non-handwriting-specialised OCR pipeline fails outright on cursive multi-line pages, while a "
    "general-purpose vision-language model handles the same pages competently without any "
    "page-specific tuning. This is a direct instance of the same lesson Track 1's rank reversal "
    "teaches from a different angle, that no single baseline characterises a task, extended here "
    "from cross-corpus to cross-architecture generalisation. Mean per-record latency was 4,830 ms "
    "for Tesseract and 7,014 ms for Florence-2-base, reported for completeness; Qwen2.5-VL, also "
    "already integrated into the harness (Table 4), is the next Track 2 baseline planned (Section 7)."
)

h2("4.4 Track 3 - Educational Assessment")
body(
    "Track 3 evaluates Gemini Flash on all 50 Mendeley exam papers, with teacher scores spanning 13 "
    "to 43 marks. Each paper is rendered as a 150 DPI PNG and given to the model with a holistic "
    "grading prompt that requests a single numeric score, with no rubric and no per-criterion "
    "breakdown provided. This is deliberately the hardest version of the task, since the model must "
    "read the handwriting and form a judgement about its quality in one pass. Free-tier API rate "
    "limits meant the 50 papers were graded across three Gemini variants (gemini-2.5-flash, "
    "gemini-flash-latest, and gemini-3.5-flash), and the combined metrics below were computed over "
    "all 50 records regardless of which variant produced the prediction, a limitation discussed "
    "further in Section 6.3."
)

add_table(
    headers=["Model", "n", "MAE (95% CI)", "Pearson r (95% CI)", "Spearman rho", "EM+-1", "EM+-5"],
    rows=[["Gemini (combined)", "50", "3.780 [2.090, 5.730]", "0.543 [0.235, 0.801]",
           "0.550", "0.580", "0.780"]],
    cap_text="Table 8. Track 3 educational assessment results on Mendeley exam papers (n=50), with "
             "bootstrap 95% confidence intervals (10,000 resamples, seed 42) on MAE and Pearson r."
)

body(
    "A Score MAE of 3.78 marks, against a 30-mark spread in the underlying data, is a reasonable "
    "outcome for a model that received no rubric at all, and a Pearson r of 0.543 confirms the "
    "model is tracking genuine signal rather than producing scores unrelated to paper quality. The "
    "EM+-5 figure of 0.780 is the more intuitive summary: four out of every five papers land within "
    "five marks of what the teacher actually gave. Where the model struggles is precision rather "
    "than direction, in that the moderate rather than strong correlation points to a model that "
    "distinguishes a strong paper from a weak one but not two papers separated by only a mark or "
    "two, which is exactly the resolution a real grading decision usually turns on."
)
body(
    "Both point estimates carry wide bootstrap 95% confidence intervals given the n = 50 sample "
    "(reported alongside each metric in Table 8). The MAE "
    "interval excludes zero by a wide margin, so the model is reliably making non-trivial errors "
    "rather than grading near-perfectly with occasional noise, and the Pearson r interval stays "
    "entirely on the positive side, so the correlation itself is unlikely to be a chance artefact of "
    "this particular 50-paper sample, even though its exact strength is not tightly pinned down. "
    "Both intervals are wide enough that this result should be read as a pilot-scale finding rather "
    "than a precise benchmark number, as discussed further in Section 6.3."
)

fig("fig06_pred_vs_actual_score.png",
    "Fig. 7. Predicted vs. actual exam score scatter plot (Track 3, n=50).")
fig("fig10_score_error_histogram.png",
    "Fig. 8. Score prediction error histogram (Track 3, n=50).")

body(
    "Fig. 7 plots predicted score against teacher score for all 50 papers. Predictions cluster "
    "tightly around the diagonal for mid-range scores, which is where most of the corpus sits, but "
    "the scatter widens noticeably at both the top and bottom of the scale. Fig. 8's error "
    "histogram, with +-3 and +-5 mark tolerance bands overlaid, gives a second view of the same "
    "result: the bulk of predictions sit comfortably inside the +-5 band, but the tail beyond it is "
    "not negligible, and it is exactly the papers in that tail that would need teacher review in any "
    "responsible deployment of this kind of grading assistant."
)

h2("4.5 Track 5 - Trustworthiness")
body(
    "Track 5 asks a different question of the same 50 papers: not only what score the model gives, "
    "but whether that score can be trusted. Gemini is prompted to return four structured fields for "
    "every paper, namely SCORE, CONFIDENCE (0-1), EVIDENCE (a direct quotation supporting the "
    "score), and REASONING. Confidence calibration is summarised with Expected Calibration Error "
    "(ECE), and discriminative ability, whether stated confidence separates correct from incorrect "
    "predictions, is summarised with AUROC, both computed against a correctness threshold of +-3 "
    "marks. As with Track 3, free-tier API limits meant Track 5 was graded across more than one "
    "Gemini variant, though a different pair than Track 3 used: gemini-3.1-flash-lite for 31 "
    "records and gemini-3.5-flash for 19 records. Combined metrics below are computed over all 50 "
    "records regardless of which variant produced the prediction, the same measurement confound "
    "discussed for Track 3 in Section 6.3."
)

add_table(
    headers=["Model", "n", "ECE (95% CI)", "AUROC (95% CI)", "Evidence Gen. Rate",
             "Reasoning Rate", "MAE"],
    rows=[["Gemini (combined)", "50", "0.251 [0.129, 0.376]", "0.571 [0.320, 0.680]",
           "1.000", "1.000", "4.120"]],
    cap_text="Table 9. Track 5 trustworthiness results on Mendeley exam papers (n=50), with "
             "bootstrap 95% confidence intervals (10,000 resamples, seed 42) on ECE and AUROC."
)

body(
    "Evidence Generation Rate and Reasoning Rate measure whether the prompt succeeds at eliciting "
    "the two supporting fields, not whether their content is accurate or actually supports the "
    "score given, and are named accordingly rather than as a 'grounding' metric, since grounding in "
    "the trustworthy-AI sense implies a verified link between the cited evidence and the model's "
    "output, which this release does not check. Evidence Generation Rate is the fraction of records "
    "for which the EVIDENCE field is non-empty and longer than five characters, and Reasoning Rate "
    "is the fraction for which the REASONING field is non-empty and longer than ten characters, "
    "both computed directly on the raw model output with no human or automated check on whether the "
    "quoted evidence actually supports the score given. Both rates are a perfect 1.000 on this "
    "basis, in that the structured prompt succeeds completely at getting the model to generate a "
    "non-empty EVIDENCE field and a non-empty REASONING field on every paper, without exception; "
    "this is a presence check on prompt compliance, not a verified-support or grounding-quality "
    "metric, and should be read accordingly. The other half of the result is less encouraging: ECE "
    "of 0.251 and AUROC of 0.571, barely above the 0.5 line marking pure chance, show that the "
    "model's stated confidence carries almost no information about whether the score it just "
    "produced is correct. The model is fluent and well organised in how it justifies itself, but "
    "that fluency is not a signal of reliability, which means a human reviewer has little cue to "
    "know which predictions deserve a second look."
)
body(
    "Both calibration statistics carry wide bootstrap 95% confidence intervals at n = 50, reported "
    "alongside each metric in Table 9. The AUROC interval "
    "straddles the 0.5 chance line, so this result cannot rule out the possibility that confidence "
    "carries some real discriminative signal the point estimate underestimates, but it equally "
    "cannot rule out chance-level performance, and either way the practical implication is the "
    "same: at this sample size, stated confidence should not be trusted to flag which predictions "
    "need a second look. Widening this dataset is the most direct way to tighten both intervals, as "
    "discussed in Section 6.3."
)

fig("fig04_auc_roc.png",
    "Fig. 9. AUC-ROC curve for Track 5 confidence calibration (AUROC = 0.571).")
fig("fig07_calibration_diagram.png",
    "Fig. 10. Reliability diagram and confidence histogram (ECE = 0.251).")

body(
    "Fig. 9's ROC curve sits close to the diagonal chance line for most of its length, which is "
    "the visual signature of confidence that does not discriminate. Fig. 10's reliability diagram "
    "makes the overconfidence concrete, in that within most confidence bins the model's empirical "
    "accuracy sits below its stated confidence, and the confidence histogram beneath it shows "
    "predictions clustering at the high-confidence end regardless of whether the underlying score "
    "was correct. This is the specific failure mode Track 5 was designed to catch, and it is one "
    "that a standard accuracy metric such as MAE would not reveal on its own."
)

h2("4.6 Track 5 Evidence Quality: A Manual Audit")
body(
    "Evidence Generation Rate, as defined in Section 4.5, measures only whether the model's EVIDENCE "
    "field is non-empty; a rate of 100% says nothing about whether that text describes something "
    "actually present in the exam image or the grade it produced. To close that gap without "
    "fabricating a large-scale annotation effort, we manually audited a stratified random sample of "
    "30 of the 50 Track 5 predictions (seed 42) against two separate questions: whether the EVIDENCE "
    "string contains a specific, checkable visual claim at all, and, if so, whether the resulting "
    "predicted score matches the teacher score. This separates evidence correctness from score "
    "correctness rather than collapsing them into one label. A prediction is classified Fully "
    "Supported if its EVIDENCE string contains a specific, checkable visual claim, a quoted number, "
    "a described mark such as a circle, checkmark, or red-ink annotation, and the predicted score "
    "matches the teacher score within 1 mark; Evidence-Supported But Score Incorrect if it contains "
    "such a claim but the predicted score does not match; and Unsupported if the evidence text "
    "contains no specific, checkable claim at all, regardless of whether the score happens to match."
)
add_table(
    headers=["Category", "Definition", "n (of 30)", "Share"],
    rows=[
        ["Fully Supported", "Specific visual claim, and predicted score matches teacher score (+-1)",
         "15", "50%"],
        ["Evidence-Supported But Score Incorrect",
         "Specific visual claim, but predicted score does not match teacher score", "15", "50%"],
        ["Unsupported", "No specific, checkable claim in the evidence text", "0", "0%"],
    ],
    cap_text="Table 10. Manual evidence-quality audit of 30 stratified-random Track 5 predictions "
             "(seed 42), classified against the corresponding scanned exam page and teacher score."
)
body(
    "Every one of the 30 audited predictions contained a specific, checkable visual claim, none "
    "fell into the Unsupported category, which rules out the most alarming possibility, that the "
    "model is inventing evidence from nothing. To confirm the audit criterion itself is sound rather "
    "than merely internally consistent, we additionally rendered and visually inspected the source "
    "page for 3 of the 30 records against their EVIDENCE text. In both incorrect cases inspected, "
    "the cited visual detail was genuinely present on the page: for MDLY-0008, the evidence "
    "correctly identifies a red-circled \"27\" on the first of a three-page script, but the true "
    "score of 25 reflects marks the model could not see on the remaining pages; for MDLY-0029, the "
    "evidence correctly identifies both a circled \"40\" and a separate \"10\" on the page, but the "
    "model's own predicted score of 16 matches neither number, indicating the failure sits in how "
    "the observed marks were aggregated into a final score, not in what the model claimed to see. "
    "This sharpens Section 6.2's overconfidence finding into a specific mechanism: Track 5's grounding "
    "failures are downstream errors in interpreting or aggregating accurately observed evidence, not "
    "fabricated citations, which is a materially different and more tractable problem for future "
    "prompting or verification work (Section 7) to target."
)

body(
    "Table 11 consolidates the headline number from each completed track into a single "
    "at-a-glance leaderboard, gathering results that otherwise sit in four separate "
    "per-track tables (Tables 5, 7, 8, and 9) and making the one remaining "
    "unpopulated track visible as an open row rather than a silent omission."
)
add_table(
    headers=["Track", "Best Model", "Headline Metric", "Value", "Caveat"],
    rows=[
        ["1. OCR Accuracy",
         "TrOCR-base (IAM) / PaddleOCR (IIIT-Word)",
         "Exact Match",
         "0.553 / 0.664",
         "Rank fully reverses across corpora (Section 4.2, Table 5)"],
        ["2. Document Understanding",
         "Florence-2-base",
         "CER / WER",
         "0.180 / 0.580",
         "Tesseract 5 fails catastrophically on the same pages (CER 6.04); n=50 (Section 4.3)"],
        ["3. Educational Assessment",
         "Gemini Flash", "MAE / Pearson r", "3.78 marks / 0.543",
         "No rubric provided; n = 50 (Section 4.4)"],
        ["4. Multi-Modal Understanding", "—", "—", "Not yet evaluated",
         "Schema-complete, no paired QA annotations yet (Section 6.3)"],
        ["5. Trustworthiness",
         "Gemini Flash", "AUROC / ECE", "0.571 / 0.251",
         "Near-chance calibration despite 100% evidence generation (Section 4.5)"],
    ],
    cap_text="Table 11. EvalBench v1 headline leaderboard, one row per track. Full per-model "
             "breakdowns are in Tables 5 (Track 1), 7 (Track 2), 8 (Track 3), and 9 (Track 5)."
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5 – ABLATION
# ══════════════════════════════════════════════════════════════════════════════
h1("5. Ablation Study")
body(
    "The results in Section 4.2 already show that EM scores shift between IAM and IIIT-Word. This "
    "ablation isolates the ranking consequence of that shift directly, since a metric can move "
    "without changing which model a practitioner would actually deploy, and it is the deployment "
    "decision, not the raw metric, that a benchmark ultimately exists to inform."
)

fig("fig14_rank_comparison.png",
    "Fig. 11. Rank reversal between IAM and IIIT-Word, Track 1 (slope chart, rank by Exact "
    "Match, 1 = best).")

body(
    "Fig. 11's slope chart is the most informative result in this ablation, plotting each model's "
    "rank on IAM against its rank on IIIT-Word directly rather than as two separate bar charts. "
    "TrOCR-base falls from rank 1 to rank 3 and PaddleOCR climbs from rank 4 to rank 1, a complete "
    "inversion of the top and bottom of the leaderboard rather than a modest reshuffling in the "
    "middle. EasyOCR is the one model whose rank holds steady at 2 across both corpora, visible as "
    "the one flat line in the chart, which is worth noting given its middling absolute scores on "
    "both. Choosing a "
    "deployment model based on IAM alone points to TrOCR-base; choosing based on IIIT-Word alone "
    "points to PaddleOCR, and those two choices cannot both be correct given that the only variable "
    "that changed between them is which corpus was used, not any difference in underlying model "
    "quality."
)
fig("fig11_wordlen_vs_cer.png",
    "Fig. 12. Word length vs. CER scatter with binned means for TrOCR-base and PaddleOCR.")
fig("fig12_latency_comparison.png",
    "Fig. 13. Model inference latency comparison across four OCR models (Apple M3, CPU).")
body(
    "The remaining diagnostic figures add model-internal detail to the ablation. Fig. 12 shows "
    "that character error rate climbs with word length for both "
    "TrOCR-base and PaddleOCR, though the two models diverge in exactly where that climb becomes "
    "steep, which hints at different failure modes between a sequence decoder and a "
    "detection-recognition pipeline. Fig. 13 adds a practical dimension often absent from "
    "accuracy-only benchmarks, namely inference latency on ordinary CPU hardware, which matters as "
    "much as raw accuracy for any institution planning to deploy OCR at the scale of an entire exam "
    "board."
)

h2("5.1 Exploratory Cross-Track Diagnostic: Document Legibility vs. Grading Error")
body(
    "One advantage a unified schema is supposed to offer over separately reported benchmarks is the "
    "ability to ask cross-track questions: does the quality of the document image feeding Track 1 "
    "help explain the errors reported in Track 3? Mendeley, the Track 3 source, has no ground-truth "
    "OCR transcription, so a true CER-based propagation analysis is not possible with the current "
    "corpus. As a lower-cost proxy, page 1 of each of the 50 scanned exam scripts was processed with "
    "Tesseract 5 (the same engine used in Track 1) to extract a mean word-confidence score and a "
    "total extracted-character count, then each was correlated against the absolute grading error "
    "(|predicted score - teacher score|) for that same script from Track 3."
)
fig("fig16_cross_track_ocr_grading.png",
    "Fig. 14. Exploratory diagnostic: page-1 extracted character count (Tesseract legibility "
    "proxy) vs. absolute Track 3 grading error, per Mendeley script (n = 50).")
body(
    "Mean OCR confidence does not correlate significantly with grading error (r = 0.194, "
    "p = 0.178). Extracted character count does, weakly (r = 0.319, p = 0.024, uncorrected for "
    "multiple comparisons), with scripts that yield more page-1 text tending toward larger grading "
    "errors. This is reported as an exploratory, hypothesis-generating result rather than a "
    "confirmed propagation effect, for three reasons stated plainly: the proxy measures Tesseract's "
    "reading of typed and handwritten content mixed together on a single page, not Gemini's own "
    "internal visual processing of the full multi-page script, so it may not reflect what actually "
    "drives Gemini's grading errors; a higher character count is at least as plausibly a proxy for "
    "longer, more complex answer scripts as for image legibility, and the current data cannot "
    "separate those two explanations; and a single correlation at p = 0.024 with n = 50 and no "
    "multiple-comparison correction is suggestive, not confirmatory. A rigorous version of this "
    "analysis, using ground-truth transcriptions of the Mendeley scripts and Gemini's own attention "
    "or confidence signals rather than a third-party OCR proxy, is named as future work in Section "
    "7. What this diagnostic does establish is that the unified schema makes the question askable "
    "at all: no existing single-track OCR or grading benchmark can even pose it, since doing so "
    "requires the same documents to carry both an OCR-quality signal and a grading-error signal "
    "under one evaluation harness."
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6 – DISCUSSION
# ══════════════════════════════════════════════════════════════════════════════
h1("6. Discussion")

h2("6.1 Multi-Source Evaluation Findings")
body(
    "The rank reversal between IAM and IIIT-Word is the central finding of this study, and it is "
    "worth restating plainly: the model ranked first on one corpus is ranked last on the other. The "
    "cross-dataset EM gap of 0.589 recorded for PaddleOCR is, on its own, larger than the total EM "
    "score achieved by three of the four models on IAM. This makes ordinary measurement noise an "
    "unlikely explanation, a conclusion the independent-samples bootstrap and permutation tests "
    "reported in Section 4.2 confirm directly (p < 0.001 for all four models except Tesseract 5 at "
    "p = 0.0005)."
)
body(
    "A laboratory that validates only on IAM would deploy TrOCR-base; one that "
    "validates only on IIIT-Word would deploy PaddleOCR instead, and the two recommendations are "
    "mutually exclusive. Because IAM and IIIT-Word are both widely used handwriting corpora rather "
    "than one being an obscure edge case, this is a warning about the ordinary practice of "
    "validating on whichever corpus happens to be convenient, not about unusual data."
)
body(
    "This carries a direct procurement implication that is easy to overlook. Vendor claims of "
    "state-of-the-art OCR accuracy are almost always benchmarked on a single reference dataset "
    "chosen by the vendor, and Table 6 shows how misleading that single number can be once "
    "deployment data differs even modestly from benchmark data. An institution evaluating "
    "handwriting recognition for its own exam scripts should, at minimum, request performance "
    "figures across more than one representative corpus before trusting a headline accuracy claim."
)

h2("6.2 Assessment and Trustworthiness Findings")
body(
    "On this 50-paper Mendeley sample, Track 3 shows that Gemini Flash can grade handwritten exam "
    "papers with no rubric and land within five marks on 78% of them. That is a genuinely useful "
    "zero-shot baseline for this specific rubric-free setup, though not one precise "
    "enough for high-stakes, unsupervised deployment."
)
body(
    "The model's weakness is specifically at the "
    "resolution that separates a 27 from a 29, not at telling a strong paper from a weak one. This "
    "suggests the gap between current performance and human-grader precision is a rubric problem as "
    "much as a model-capability problem, a hypothesis Section 7 returns to directly."
)
body(
    "Track 5's result is the sharper of the two findings, precisely because it would remain "
    "invisible to anyone looking only at MAE. A model can cite specific supporting evidence for "
    "every prediction it makes and still carry a confidence score with almost no relationship to "
    "whether that prediction is correct. Evidence generation and calibration are, empirically, "
    "decoupled properties, and evaluating one without the other risks certifying a grading tool as "
    "reliable when only its explanatory fluency, not its actual judgement, has been checked."
)

h2("6.3 Limitations")
body(
    "First, the Track 3 and Track 5 results are each combined across more than one Gemini model "
    "variant because free-tier API quotas were exhausted mid-evaluation. The two tracks were "
    "not even affected the same way: Track 3 spans three variants (gemini-2.5-flash, "
    "gemini-flash-latest, gemini-3.5-flash), while Track 5 spans a different pair "
    "(gemini-3.1-flash-lite, gemini-3.5-flash)."
)
body(
    "This introduces a measurement confound in both "
    "tracks, since some of the variance in the combined results may reflect differences between "
    "model versions rather than genuine task difficulty, and it is the single highest-priority item "
    "for the next release: a controlled replication running one fixed Gemini version, fixed prompt, "
    "fixed temperature, fixed image resolution, and a fixed seed across all 50 papers for both "
    "Track 3 and Track 5, under the identical evaluation protocol already implemented in this "
    "release's harness. We would not expect a single-version rerun to overturn the qualitative "
    "findings, since the overconfidence pattern (AUROC close to 0.5) and the imperfect grading "
    "accuracy (MAE around 3-4 marks) are consistent enough across the variants already sampled that "
    "they are unlikely to be an artefact of any one version; what a fixed-version rerun would mainly "
    "change is the width of the confidence intervals reported in Table 8 and Table 9, not their "
    "central tendency. That expectation is a hypothesis, not a result, and the numbers in this "
    "release should be treated as provisional until it is checked."
)
body(
    "Second, 50 papers is a small sample for calibration statistics specifically. The bootstrap 95% "
    "confidence interval around Track 5's AUROC (0.320 to 0.680) spans almost the entire plausible "
    "range for a discrimination metric, and the interval around ECE (0.129 to 0.376) is similarly "
    "wide. This means the Track 5 numbers should be read as a directional signal, namely that the "
    "model is overconfident, rather than as a tightly bounded estimate of exactly how overconfident."
)
body(
    "Third, Track 2 (document understanding) now has two baselines (Section 4.3), spanning a "
    "classical OCR engine (Tesseract 5) and an open vision-language model (Florence-2-base), but "
    "both are evaluated on n = 50 records from only one of Track 2's three named sources, IIIT "
    "English Page, with anshcode1 held out as unlabelled and gopika13 lacking the modality Track 2 "
    "needs. The two results diverge sharply, catastrophic failure for Tesseract against a "
    "competitive Character Accuracy of 0.820 for Florence-2, which is itself informative about "
    "architecture choice for page-level document understanding, but a two-model, single-source "
    "comparison should not be read as a settled ranking; broadening both the baseline set and the "
    "source coverage is the most immediate item on the roadmap in Section 7."
)
body(
    "Track 4 (multi-modal understanding) remains genuinely blocked rather than merely "
    "under-evaluated. It is defined in the EvalBench schema against gopika13 and the IEEE Answer "
    "Sheet Dataset, but direct inspection of the processed corpus this release confirms that "
    "gopika13 supplies handwriting-sample images without the paired question-answer annotations "
    "multi-modal question answering requires, and the IEEE source has not yet been downloaded. This "
    "is a labelled-data gap, not an engineering gap: there is currently no way to construct a Track "
    "4 evaluation set from data already in this release, and closing it is the most immediate item "
    "on the roadmap in Section 7."
)
body(
    "The five-track leaderboard is therefore four-fifths populated in this release, with Track 2 "
    "carrying an important caveat of its own. This is exactly the gap the pilot-release label in the "
    "title and abstract is meant to signal. EvalBench v1 defines the full five-track schema up "
    "front, deliberately, so that each track can be filled in against a fixed, already-published "
    "interface rather than bolted on after the fact, but it reports experimental results only for "
    "the tracks that have the labelled data a genuine evaluation requires, rather than padding the "
    "leaderboard with placeholder baselines."
)
body(
    "Fourth, the dataset statistics in Fig. 15 make clear that the corpus is heavily weighted "
    "toward word-level OCR data (Fig. 15 uses a log scale on the record-count axis, since the "
    "sources span three orders of magnitude, from 50 to over 85,000 records). IIIT-Word alone "
    "contributes 85,020 records and IAM a further 38,305, while Mendeley, the only source with "
    "genuine graded ground truth, contributes just 50. Balancing this distribution, most plausibly "
    "by extending the graded-assessment side of the corpus, would make EvalBench a more even test "
    "of all five tracks."
)
body(
    "Fifth, statistical uncertainty is now quantified but remains wide at this sample size. "
    "Sections 4.2 through 4.5 report bootstrap 95% confidence intervals and, for Track 1, "
    "independent-samples permutation tests alongside every headline number. The Track 1 EM gaps are "
    "all statistically significant at p < 0.001 (Tesseract 5 at p = 0.0005)."
)
body(
    "The Track 3 and Track 5 "
    "intervals are considerably wider, reflecting the n = 50 sample those two tracks are built on. "
    "They should be read as evidence that the reported effects are real, rather than as a precise "
    "estimate of their exact magnitude. Growing the graded-assessment portion of the corpus beyond "
    "50 papers is the most direct way to tighten those intervals in the next release."
)

fig("fig09_dataset_statistics.png",
    "Fig. 15. EvalBench v1 dataset statistics (total vs. test split per source).")

h2("6.4 Threats to Validity")
body(
    "Beyond the limitations above, three validity concerns are worth flagging for readers planning "
    "to build on this work."
)
body(
    "The internal validity of the Track 1 comparison depends on test subsets "
    "of 133 to 223 records per model, after the three-character reference-length filter is applied "
    "to IAM and IIIT-Word, sampled from full test splits of 7,661 (IAM) and 17,004 (IIIT-Word) "
    "records. The sample was capped rather than exhaustive because all four OCR models were run "
    "CPU-only, and per-image latency ranges up to 787 ms for TrOCR-base and 664 ms for EasyOCR on "
    "IIIT-Word (Table 5, Fig. 13); evaluating the full test splits across four models on CPU would "
    "extend a pilot-release evaluation into a multi-day run, which is why v1 reports a fixed sample "
    "and treats a full-split re-run as a v1.1 scale-up rather than a v1 requirement. A larger "
    "held-out sample would tighten the confidence bounds around "
    "the reported EM gaps; PaddleOCR's smaller, non-matched sample (Section 4.2) compounds this for "
    "that model specifically, and its EM gap should be weighted accordingly until the batches are "
    "re-run at a matched sample size."
)
body(
    "The external validity of the Track 3 and "
    "Track 5 findings is bounded by a single source of graded ground truth: the Mendeley dataset, "
    "collected under one grading rubric and one national examination context. The specific "
    "magnitude of the overconfidence pattern reported here should not be assumed to transfer "
    "unchanged to other grading systems, subjects, or countries without direct testing."
)
body(
    "Construct "
    "validity is a live question for Track 5 specifically: a model's willingness to cite a "
    "plausible-looking quotation is treated here as evidence generation. A perfect Evidence "
    "Generation Rate does not by itself confirm that the cited evidence is the actual basis for the "
    "score, rather than a "
    "fluent justification generated after the score was already decided — a distinction that Section "
    "7 identifies as a direction for future work."
)

h2("6.5 Why Standardised, Multi-Track Benchmarking Matters")
body(
    "Both headline findings in this paper share a structural property worth naming directly: neither "
    "would have been visible to a single-task evaluation. The IAM/IIIT-Word rank reversal in Section "
    "4.2 only becomes an argument for multi-corpus OCR evaluation because Track 1 tests every model "
    "against both datasets under one metric set. A paper reporting IAM results alone, the more "
    "common practice, would have published exactly the wrong deployment recommendation, with no way to "
    "detect the error internally."
)
body(
    "The Track 5 calibration-decoupling result in Section 6.2 is even more "
    "dependent on joint evaluation: a model can produce a fluent evidence citation for every "
    "prediction while its stated confidence still carries almost no signal about correctness. That gap "
    "is only measurable because Track 5 evaluates score accuracy, evidence generation, and "
    "calibration as three separate, simultaneous properties, rather than as three unrelated papers. "
    "This is "
    "the practical case for treating EvalBench as evaluation infrastructure rather than as a "
    "collection of individually reproducible baselines. The value is not in any single track's "
    "numbers, but in what only becomes visible once OCR, grading, and trustworthiness are evaluated "
    "within one schema and reproducible harness, with cross-track analysis enabled where shared "
    "documents are available, as in the exploratory OCR-legibility proxy on the Mendeley papers in "
    "Section 5.1. The five tracks in this release draw on largely disjoint corpora rather than one "
    "shared set of documents end to end, so the claim here is architectural, that the schema makes "
    "cross-track comparison possible and, where document overlap exists, directly measurable, not "
    "that every track in v1 is already evaluated on the identical set of source documents."
)
body(
    "EvalBench is an evaluation-infrastructure contribution rather than a new model: it introduces "
    "no new OCR architecture, grading model, or training procedure, and every model reported here is "
    "an existing, off-the-shelf system. In the tradition of GLUE, SuperGLUE, and OCRBench, its "
    "primary contributions are task coverage, reproducibility of the evaluation protocol, "
    "standardisation of metrics across otherwise incomparable systems, and identification of failure "
    "modes that single-task benchmarks do not reveal, such as the rank reversal in Section 4.2, the "
    "architecture-dependent Track 2 gap in Section 4.3, and the calibration-decoupling result in "
    "Section 6.2."
)

h2("6.6 Practical Impact")
body(
    "Sections 4 and 5 report each track's finding on its own terms, metrics, confidence intervals, "
    "and statistical tests; this subsection translates those findings into what they would mean for "
    "someone deploying these systems, without introducing any new result. Fig. 16 lines up each "
    "track's headline finding against its deployment implication."
)
fig("fig18_impact_diagram.png",
    "Fig. 16. From reported finding to deployment implication, one row per track. Every finding "
    "cited is reported in full, with statistics and confidence intervals, in the section noted.")
body(
    "Read together, the five rows make a single argument concrete: accuracy-only, single-corpus "
    "evaluation would have certified TrOCR-base and Track 5's calibration as deployment-ready, when "
    "neither claim survives the additional tracks EvalBench adds. That is the practical case for "
    "unified, multi-track evaluation stated in terms an engineering team, not only a benchmark "
    "reviewer, would act on."
)

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7 – CONCLUSION
# ══════════════════════════════════════════════════════════════════════════════
h1("7. Conclusion and Future Work")
body(
    "This paper introduced EvalBench v1 as a pilot release, a unified multi-task evaluation "
    "framework for reliable AI-based educational document processing, built from 132,891 "
    "quality-filtered records across six datasets (123,325 of them word-level OCR crops, and 50 "
    "carrying genuine teacher-assigned grades) and organised into five evaluation tracks, four of "
    "which are experimentally complete "
    "in this release. The central experimental result, a rank reversal between IAM and IIIT-Word "
    "large enough to flip a deployment decision entirely, demonstrates that multi-source evaluation "
    "is essential for avoiding corpus-dependent deployment decisions, in that identical models "
    "produce opposite recommendations depending solely on which corpus is used to judge them."
)
body(
    "The Track 5 result adds "
    "a second, independent lesson: structured, well-justified output and genuinely calibrated "
    "confidence are separate properties, and a system can excel at one while failing the other. On "
    "this evidence, Gemini Flash under a no-rubric holistic prompt is not yet ready for unsupervised, "
    "high-stakes grading, and the same evaluation pattern is worth applying to any AI grading tool "
    "before it is deployed in a real classroom."
)
body(
    "Nine directions follow from the limitations catalogued in Sections 5.1 and 6.3, listed "
    "below in order of urgency."
)
future_directions = [
    "Resolve the model-consistency confound in Tracks 3 and 5 by re-running each full 50-paper "
    "evaluation on one fixed Gemini version instead of the several variants each track currently "
    "mixes together, which would remove the largest source of measurement noise currently "
    "affecting the calibration metrics.",

    "Unblock Track 4 and broaden Track 2's source coverage. Track 4 is defined in the EvalBench "
    "schema against gopika13 and the IEEE Answer Sheet Dataset, but gopika13 supplies handwriting "
    "images without the paired question-answer annotations multi-modal question answering requires, "
    "and the IEEE source has not yet been downloaded; acquiring either labelled data source is a "
    "prerequisite for any Track 4 baseline, not an implementation task. Track 2, by contrast, now "
    "has two baselines (Tesseract 5 and Florence-2-base, Section 4.3), but both are evaluated on "
    "only one of its three named sources; annotating the currently unlabelled anshcode1 records and "
    "running Qwen2.5-VL, already integrated into the harness (Table 4) and reusable on Track 2 "
    "without new engineering, would extend Track 2's two-model comparison to a broader, more "
    "source-diverse baseline suite and complete the five-track leaderboard.",

    "Add rubric-grounded prompting for Track 3. The current protocol deliberately withholds any "
    "rubric, which is useful for measuring a lower bound on zero-shot capability but understates "
    "what these models can do when given the same grading criteria a human teacher would use. "
    "Supplying structured, per-criterion rubrics and re-measuring MAE would test directly whether "
    "the fine-grained allocation weakness identified in Section 6.2 is a genuine capability "
    "ceiling or an artefact of an underspecified prompt.",

    "Extend linguistic breadth. EvalBench v1 is English-only, which leaves out a large share of "
    "the world's classrooms where instruction and assessment happen in Tamil, Arabic, Chinese, or "
    "another script entirely. Extending the corpus with graded handwriting samples in additional "
    "languages would test whether the rank-reversal and overconfidence patterns reported here are "
    "properties of these particular models and datasets, or something closer to a general "
    "property of how vision-language systems behave under handwriting-heavy, high-stakes "
    "educational tasks regardless of language.",

    "Broaden the baseline set beyond a single VLM family. Track 3 and Track 5 currently report "
    "Gemini Flash only; adding two or three additional vision-language models (for example "
    "GPT-4o, Qwen2.5-VL, or Florence-2) under the same rubric-free protocol would let the "
    "rank-reversal-style analysis in Section 5 extend to grading and calibration, not only OCR, "
    "and would directly address the most common reviewer question a single-model grading result "
    "invites.",

    "Add an inter-rater agreement baseline for Track 3. The current design compares Gemini Flash "
    "against one teacher's score per paper; measuring teacher-versus-teacher agreement on a "
    "subset of the same papers would show whether Gemini's 3.78-mark MAE is competitive with "
    "human-to-human disagreement or falls meaningfully short of it, which the current single-rater "
    "design cannot establish either way.",

    "Move evidence-quality checking from presence to correctness. Evidence Generation Rate "
    "(Section 4.5) currently confirms only that the EVIDENCE field is non-empty, not that the "
    "quoted text actually supports the assigned score. A human or automated check of whether cited "
    "evidence is faithful to the source document, on even a sampled subset of predictions, would "
    "convert this from a prompt-compliance metric into a genuine grounding metric.",

    "Replace the OCR-legibility proxy in Section 5.1 with a rigorous cross-track propagation "
    "analysis. Doing so needs ground-truth transcriptions for the Mendeley scripts (currently "
    "absent) so that a true CER can be computed per script, and ideally a confidence or attention "
    "signal from Gemini's own visual processing rather than a third-party OCR engine reading a "
    "single page in isolation. That would convert Section 5.1's exploratory, hypothesis-generating "
    "correlation into a confirmatory test of whether OCR quality causally propagates into grading "
    "error, which is the strongest possible use of a schema that already spans both tracks.",

    "Develop a principled composite benchmark score. Table 11 lists one headline number per track, "
    "but the five tracks' metrics, Character Accuracy, Pearson correlation, and AUROC, are not "
    "currently on a comparable scale or footing, and an arbitrarily weighted average across them "
    "would misrepresent precision the schema does not yet support. A composite index is left for "
    "future work until Track 2 has a broader, source-diverse baseline suite and Track 4 has any "
    "baseline at all, at which point a defensible cross-track weighting scheme can be established "
    "on real evidence rather than assumed.",
]
for direction in future_directions:
    p = doc.add_paragraph(direction, style="List Number")
    p.paragraph_format.space_after = Pt(4)
    for run in p.runs:
        run.font.size = Pt(11)
body(
    "Beyond these directions, the broader engineering motivation for a benchmark like EvalBench "
    "is standardisation. Educational AI vendors and institutions currently have no shared, "
    "reproducible way to compare an OCR component, a grading model, and a confidence-estimation "
    "layer against the same corpus, split protocol, and metric definitions, which makes vendor "
    "claims and internal validation results difficult to compare across teams or across procurement "
    "cycles. A common schema and evaluation harness, released publicly with fixed splits, gives "
    "institutions a way to reproduce a vendor's reported numbers rather than take them on faith, and "
    "gives researchers a fixed target against which future OCR and vision-language systems can be "
    "compared on equal footing rather than on whichever corpus a paper happens to report."
)
body(
    "That "
    "shared basis is also a precondition for safer deployment: the rank-reversal and overconfidence "
    "findings in this paper are only visible because OCR, grading, and calibration were evaluated "
    "under one protocol instead of three separate ones, and a procurement or deployment decision "
    "made without that kind of joint evaluation risks missing exactly the failure modes that matter "
    "most before an AI grading tool reaches a real classroom."
)

# ══════════════════════════════════════════════════════════════════════════════
#  END-MATTER  (required by most Q1 / Elsevier-style journals)
# ══════════════════════════════════════════════════════════════════════════════
body(
    "Author contact information and the CRediT authorship contribution statement are provided in "
    "the accompanying title page document, in line with this journal's anonymous peer review "
    "process, and are not reproduced here."
)

h1("Declaration of Competing Interest")
body(
    "The authors declare that they have no known competing financial interests or personal "
    "relationships that could have appeared to influence the work reported in this paper."
)

h1("Data and Code Availability")
body(
    "All six source datasets used to construct EvalBench v1 are publicly available from their "
    "original repositories, as cited in Section 3 and the reference list. The EvalBench v1 corpus, "
    "the JSON Schema v2.0 specification, all evaluation scripts, and the full experimental outputs "
    "reported in this paper will be released at the time of publication to support independent "
    "verification and reuse. Because IAM is distributed under a license that requires individual "
    "registration and restricts redistribution of its images, the public release will include IAM "
    "and IIIT English Word records as derived annotations and licensed-source pointers rather than "
    "as re-hosted raw images, so that redistribution stays within each source dataset's own terms."
)

h1("Declaration of generative AI and AI-assisted technologies in the manuscript preparation process")
body(
    "During the preparation of this work, the author(s) used Claude (Anthropic) in order to assist "
    "with improving language, wording, organisation, and readability, to support literature search "
    "and citation verification, and to cross-check computed statistics against source data. After "
    "using this tool/service, the author(s) reviewed and edited the content as needed and take(s) "
    "full responsibility for the content of the published article."
)

# ══════════════════════════════════════════════════════════════════════════════
#  REFERENCES  (Elsevier Harvard style, alphabetical by first-author surname)
# ══════════════════════════════════════════════════════════════════════════════
h1("References")

REFERENCES = [
    dict(authors="Aisyah, N., Al Kautsar, M.D., Hidayat, A., Chowdhury, R., Koto, F.", year="2025",
         title="From Handwriting to Feedback: Evaluating VLMs and LLMs for AI-Powered Assessment in "
               "Indonesian Classrooms",
         journal="arXiv preprint", doi="arXiv:2506.04822"),
    dict(authors="Bai, J., Bai, S., Yang, S., Wang, S., Tan, S., Wang, P., Lin, J., Zhou, C., Zhou, J.",
         year="2023",
         title="Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text "
               "Reading, and Beyond",
         journal="arXiv preprint", doi="arXiv:2308.12966"),
    dict(authors="Chen, Z., Wu, J., Wang, W., Su, W., Chen, G., Xing, S., Zhong, M., Zhang, Q., Zhu, X., "
               "Lu, L., Li, B., Luo, P., Lu, T., Qiao, Y., Dai, J.", year="2024",
         title="InternVL: Scaling up Vision Foundation Models and Aligning for Generic Visual-Linguistic "
               "Tasks",
         journal="Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition "
                 "(CVPR 2024), 24185-24198",
         doi="arXiv:2312.14238"),
    dict(authors="Cohen, J.", year="1960",
         title="A Coefficient of Agreement for Nominal Scales",
         journal="Educational and Psychological Measurement, 20(1), 37-46",
         doi="https://doi.org/10.1177/001316446002000104"),
    dict(authors="Cong, L., Hahn, S., Gombert, S., Camus, L., Drachsler, H., Kroehne, U.", year="2026",
         title="Confidence Estimation in Automatic Short Answer Grading with LLMs",
         journal="Springer Lecture Notes in Computer Science (AIED 2026)",
         doi="https://doi.org/10.1007/978-3-032-29755-6_8"),
    dict(authors="Crosilla, G., Klic, L., Colavizza, G.", year="2025",
         title="Benchmarking Large Language Models for Handwritten Text Recognition",
         journal="Journal of Documentation, 81(7), 334-354",
         doi="https://doi.org/10.1108/jd-03-2025-0082"),
    dict(authors="Devlin, J., Chang, M.W., Lee, K., Toutanova, K.", year="2019",
         title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
         journal="Proceedings of the 2019 Conference of the North American Chapter of the Association "
                 "for Computational Linguistics: Human Language Technologies (NAACL-HLT), 4171-4186",
         doi=""),
    dict(authors="Dinesh, K.P.", year="2026",
         title="A Dataset of Digitized Student Examination Papers, Answer Keys, and Manual Evaluations "
               "for Automated Grading Research",
         journal="Mendeley Data",
         doi="https://doi.org/10.17632/sf3kvjwknt.1"),
    dict(authors="Efron, B., Tibshirani, R.J.", year="1994",
         title="An Introduction to the Bootstrap",
         journal="Chapman & Hall/CRC",
         doi="https://doi.org/10.1007/978-1-4899-4541-9"),
    dict(authors="Eneye, T.A.N.F., Ijezue, C.F., Amjad, A.I., Amjad, M., Butt, S., Castaneda-Garza, G.",
         year="2025",
         title="Advances in Auto-Grading with Large Language Models: A Cross-Disciplinary Survey",
         journal="Proceedings of the 20th Workshop on Innovative Use of NLP for Building Educational "
                 "Applications, ACL 2025",
         doi="https://aclanthology.org/2025.bea-1.35"),
    dict(authors="Ferrer, R., Turgut, D., Chen, Z., Sonkar, S.", year="2026",
         title="When Can We Trust LLM Graders? Calibrating Confidence for Automated Assessment",
         journal="arXiv preprint", doi="arXiv:2603.29559"),
    dict(authors="Gao, P., Song, X., Wu, X., Zhu, D., Shen, S., Wang, S., Wei, W., Yang, C., Zhang, S., "
               "Li, W., Wang, B., Lin, D., Wu, L., He, C.", year="2025",
         title="PM4Bench: Benchmarking Large Vision-Language Models with Parallel Multilingual "
               "Multi-Modal Multi-task Corpus",
         journal="arXiv preprint", doi="arXiv:2503.18484"),
    dict(authors="Garrido-Munoz, C., Rios-Vila, A., Calvo-Zaragoza, J.", year="2025",
         title="Handwritten Text Recognition: A Survey",
         journal="arXiv preprint", doi="arXiv:2502.08417"),
    dict(authors="Gawlikowski, J., Tassi, C.R.N., Ali, M., Lee, J., Humt, M., Feng, J., Kruspe, A., "
               "Triebel, R., Jung, P., Roscher, R., Shahzad, M., Yang, W., Bamler, R., Zhu, X.X.",
         year="2023",
         title="A Survey of Uncertainty in Deep Neural Networks",
         journal="Artificial Intelligence Review, 56, 1513-1589",
         doi="arXiv:2107.03342"),
    dict(authors="Gemini Team, Google DeepMind", year="2023",
         title="Gemini: A Family of Highly Capable Multimodal Models",
         journal="arXiv preprint", doi="arXiv:2312.11805"),
    dict(authors="Grabowski, H.", year="2026",
         title="Towards Fully Automated Exam Grading: Fairness-Aware Recognition of Handwritten "
               "Answers with Foundation Models",
         journal="arXiv preprint", doi="arXiv:2606.11477"),
    dict(authors="Guo, C., Pleiss, G., Sun, Y., Weinberger, K.Q.", year="2017",
         title="On Calibration of Modern Neural Networks",
         journal="Proceedings of the 34th International Conference on Machine Learning (ICML), PMLR "
                 "70, 1321-1330",
         doi=""),
    dict(authors="Haller, S., Aldea, A., Seifert, C., Strisciuglio, N.", year="2022",
         title="Survey on Automated Short Answer Grading with Deep Learning: from Word Embeddings to "
               "Transformers",
         journal="arXiv preprint", doi="arXiv:2204.03503"),
    dict(authors="Hamdi, L., Tamasna, A., Boisson, P., Paquet, T.", year="2025",
         title="PILOT: A Promptable Interleaved Layout-aware OCR Transformer",
         journal="arXiv preprint", doi="arXiv:2504.03621"),
    dict(authors="Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., Steinhardt, J.",
         year="2020",
         title="Measuring Massive Multitask Language Understanding",
         journal="arXiv preprint", doi="arXiv:2009.03300"),
    dict(authors="Heusel, M., Ramsauer, H., Unterthiner, T., Nessler, B., Hochreiter, S.", year="2017",
         title="GANs Trained by a Two Time-Scale Update Rule Converge to a Local Nash Equilibrium",
         journal="Advances in Neural Information Processing Systems (NeurIPS) 30",
         doi="arXiv:1706.08500"),
    dict(authors="Huang, L., Yu, W., Ma, W., Zhong, W., Feng, Z., Wang, H., Chen, Q., Peng, W., Feng, X., "
               "Qin, B., Liu, T.", year="2023",
         title="A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, "
               "and Open Questions",
         journal="arXiv preprint", doi="arXiv:2311.05232"),
    dict(authors="Huang, Y., Lv, T., Cui, L., Lu, Y., Wei, F.", year="2022",
         title="LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking",
         journal="Proceedings of the 30th ACM International Conference on Multimedia, 4083-4091",
         doi="arXiv:2204.08387"),
    dict(authors="JaidedAI", year="2020",
         title="EasyOCR: Ready-to-Use OCR with 80+ Supported Languages",
         journal="GitHub repository",
         doi="https://github.com/JaidedAI/EasyOCR"),
    dict(authors="Kim, G., Hong, T., Yim, M., Nam, J., Park, J., Yim, J., Hwang, W., Yun, S., Han, D., "
               "Park, S.", year="2022",
         title="OCR-Free Document Understanding Transformer",
         journal="Proceedings of the European Conference on Computer Vision (ECCV 2022), 498-517",
         doi="arXiv:2111.15664"),
    dict(authors="Li, M., Lv, T., Chen, J., Cui, L., Lu, Y., Florencio, D., Zhang, C., Li, Z., Wei, F.",
         year="2023",
         title="TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models",
         journal="Proceedings of the AAAI Conference on Artificial Intelligence, 37(11), 13094-13102",
         doi="arXiv:2109.10282"),
    dict(authors="Liang, P., Bommasani, R., Lee, T., Tsipras, D., Soylu, D., Yasunaga, M., Zhang, Y., "
               "Narayanan, D., Wu, Y., Kumar, A., et al.", year="2022",
         title="Holistic Evaluation of Language Models",
         journal="arXiv preprint", doi="arXiv:2211.09110"),
    dict(authors="Liew, P.Y., Tan, I.K.T.", year="2024",
         title="On Automated Essay Grading Using Large Language Models",
         journal="Proceedings of CSAI 2024, ACM",
         doi="https://doi.org/10.1145/3709026.3709030"),
    dict(authors="Lin, C.C., Huang, A.Y.Q., Lu, O.H.T.", year="2023",
         title="Artificial Intelligence in Intelligent Tutoring Systems Toward Sustainable Education: A "
               "Systematic Review",
         journal="Smart Learning Environments, 10, Article 41",
         doi="https://doi.org/10.1186/s40561-023-00260-y"),
    dict(authors="Liu, H., Li, C., Wu, Q., Lee, Y.J.", year="2023",
         title="Visual Instruction Tuning",
         journal="Advances in Neural Information Processing Systems (NeurIPS) 36",
         doi="arXiv:2304.08485"),
    dict(authors="Liu, X., Chen, T., Da, L., Chen, C., Lin, Z., Wei, H.", year="2025",
         title="Uncertainty Quantification and Confidence Calibration in Large Language Models: A "
               "Survey",
         journal="arXiv preprint", doi="arXiv:2503.15850"),
    dict(authors="Liu, Y., Li, Z., Huang, M., Yang, B., Yu, W., Li, C., Yin, X., Liu, C., Jin, L., "
               "Bai, X.", year="2024",
         title="OCRBench: On the Hidden Mystery of OCR in Large Multimodal Models",
         journal="Science China Information Sciences",
         doi="https://doi.org/10.1007/s11432-024-4235-6"),
    dict(authors="Marti, U.V., Bunke, H.", year="2002",
         title="The IAM-database: An English Sentence Database for Offline Handwriting Recognition",
         journal="International Journal on Document Analysis and Recognition, 5(1), 39-46",
         doi="https://doi.org/10.1007/s100320200071"),
    dict(authors="Mishra, A., Alahari, K., Jawahar, C.V.", year="2012",
         title="Scene Text Recognition using Higher Order Language Priors",
         journal="Proceedings of the British Machine Vision Conference (BMVC 2012)",
         doi=""),
    dict(authors="Misgna, H., On, B.W., Lee, I., Choi, G.S.", year="2024",
         title="A Survey on Deep Learning-Based Automated Essay Scoring and Feedback Generation",
         journal="Artificial Intelligence Review, 58(2), 1-40",
         doi="https://doi.org/10.1007/s10462-024-11017-5"),
    dict(authors="Nagasubramanian, A., Almazyad, A.S., Balakrishnan, S.A., Bharath Ram, M.M., Potti, D., "
               "Zakariah, M., AlSekait, D.M.", year="2025",
         title="OCRNet: A Robust Deep Learning Framework for Alphanumeric Character Recognition to "
               "Assist the Visually Impaired",
         journal="Scientific Reports, 15, Article 41344",
         doi="https://doi.org/10.1038/s41598-025-25278-9"),
    dict(authors="OpenAI", year="2023",
         title="GPT-4 Technical Report",
         journal="arXiv preprint", doi="arXiv:2303.08774"),
    dict(authors="PaddleOCR Team", year="2025",
         title="PaddleOCR 3.0 Technical Report",
         journal="arXiv preprint", doi="arXiv:2507.05595"),
    dict(authors="Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., Killeen, T., "
               "Lin, Z., Gimelshein, N., Antiga, L., Desmaison, A., Kopf, A., Yang, E., DeVito, Z., "
               "Raison, M., Tejani, A., Chilamkurthy, S., Steiner, B., Fang, L., Bai, J., Chintala, S.",
         year="2019",
         title="PyTorch: An Imperative Style, High-Performance Deep Learning Library",
         journal="Advances in Neural Information Processing Systems (NeurIPS) 32, 8024-8035",
         doi=""),
    dict(authors="Smith, R.", year="2007",
         title="An Overview of the Tesseract OCR Engine",
         journal="Proceedings of the Ninth International Conference on Document Analysis and "
                 "Recognition (ICDAR 2007), 629-633",
         doi="https://doi.org/10.1109/ICDAR.2007.4376991"),
    dict(authors="Shi, B., Bai, X., Yao, C.", year="2016",
         title="An End-to-End Trainable Neural Network for Image-Based Sequence Recognition and Its "
               "Application to Scene Text Recognition",
         journal="IEEE Transactions on Pattern Analysis and Machine Intelligence, 39(11), 2298-2304",
         doi=""),
    dict(authors="Song, Y., Zhu, Q., Wang, H., Zheng, Q.", year="2024",
         title="Automated Essay Scoring and Revising Based on Open-Source Large Language Models",
         journal="IEEE Transactions on Learning Technologies",
         doi="https://doi.org/10.1109/TLT.2024.3396873"),
    dict(authors="Srivastava, A., Rastogi, A., Rao, A., Shoeb, A.A.M., Abid, A., Fisch, A., Brown, A.R., "
               "Santoro, A., et al.", year="2023",
         title="Beyond the Imitation Game: Quantifying and Extrapolating the Capabilities of Language "
               "Models",
         journal="Transactions on Machine Learning Research",
         doi="arXiv:2206.04615"),
    dict(authors="Su, J., Yan, X., Fu, Y., Zhang, H., Ye, Q., Liu, X., Huo, Y., Zhou, C., Hu, X.",
         year="2025",
         title="EssayJudge: A Multi-Granular Benchmark for Assessing Automated Essay Scoring "
               "Capabilities of Multimodal Large Language Models",
         journal="arXiv preprint", doi="arXiv:2502.11916"),
    dict(authors="Taghipour, K., Ng, H.T.", year="2016",
         title="A Neural Approach to Automated Essay Scoring",
         journal="Proceedings of the 2016 Conference on Empirical Methods in Natural Language "
                 "Processing (EMNLP), 1882-1891",
         doi=""),
    dict(authors="Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., "
               "Kaiser, L., Polosukhin, I.", year="2017",
         title="Attention Is All You Need",
         journal="Advances in Neural Information Processing Systems (NeurIPS) 30",
         doi="arXiv:1706.03762"),
    dict(authors="Wang, A., Singh, A., Michael, J., Hill, F., Levy, O., Bowman, S.R.", year="2018",
         title="GLUE: A Multi-Task Benchmark and Analysis Platform for Natural Language Understanding",
         journal="Proceedings of the 2018 EMNLP Workshop BlackboxNLP",
         doi="arXiv:1804.07461"),
    dict(authors="Wang, A., Pruksachatkun, Y., Nangia, N., Singh, A., Michael, J., Hill, F., Levy, O., "
               "Bowman, S.R.", year="2019",
         title="SuperGLUE: A Stickier Benchmark for General-Purpose Language Understanding Systems",
         journal="Advances in Neural Information Processing Systems (NeurIPS) 32",
         doi="arXiv:1905.00537"),
    dict(authors="Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P., "
               "Rault, T., Louf, R., Funtowicz, M., et al.", year="2020",
         title="Transformers: State-of-the-Art Natural Language Processing",
         journal="Proceedings of the 2020 Conference on Empirical Methods in Natural Language "
                 "Processing: System Demonstrations (EMNLP), 38-45",
         doi="arXiv:1910.03771"),
    dict(authors="Xiao, B., Wu, H., Xu, W., Dai, X., Hu, H., Lu, Y., Zeng, M., Liu, C., Yuan, L.",
         year="2024",
         title="Florence-2: Advancing a Unified Representation for a Variety of Vision Tasks",
         journal="Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition "
                 "(CVPR 2024)",
         doi="arXiv:2311.06242"),
    dict(authors="Xie, L., Liu, H., Zeng, J., Tang, X., Han, Y., Luo, C., Huang, J., Li, Z., Wang, S., "
               "He, Q.", year="2024",
         title="A Survey of Calibration Process for Black-Box LLMs",
         journal="arXiv preprint", doi="arXiv:2412.12767"),
    dict(authors="Yao, R., Zhang, B., Huang, J., Long, X., Zhang, Y., Zou, T., Wu, Y., Su, S., Xu, Y., "
               "Zeng, W., Yang, Z., Li, G., Zhang, S., Li, Z., Chen, Y., Xiong, S., Xu, P., Zhang, J., "
               "Zhou, B., Clifton, D., Van Gool, L.", year="2025",
         title="LENS: Multi-level Evaluation of Multimodal Reasoning with Large Language Models",
         journal="arXiv preprint", doi="arXiv:2505.15616"),
    dict(authors="Yu, Z., et al.", year="2026",
         title="Evaluating AI Grading on Real-World Handwritten College Mathematics: A Large-Scale "
               "Study Toward a Benchmark",
         journal="arXiv preprint",
         doi="https://consensus.app/papers/details/1463470b6aaa5741a378b1504228cbd9/"),
]

REFERENCES.sort(key=lambda r: surname_key(r["authors"]))
for r in REFERENCES:
    ref(r["authors"], r["year"], r["title"], r["journal"], r.get("doi", ""))

# ══════════════════════════════════════════════════════════════════════════════
#  SAVE
# ══════════════════════════════════════════════════════════════════════════════
doc.save(OUT_PATH)
print(f"Saved: {OUT_PATH}")
