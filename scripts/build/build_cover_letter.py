"""
Build the EAAI submission cover letter as a .docx file.
Run:  python3 evalbench_paper2/paper_draft/build_cover_letter.py
"""

from __future__ import annotations
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT     = Path(__file__).parent.parent.parent
OUT_PATH = ROOT / "evalbench_paper2/paper_draft/EvalBench_CoverLetter.docx"

doc = Document()

section = doc.sections[0]
section.top_margin    = Inches(1.0)
section.bottom_margin = Inches(1.0)
section.left_margin   = Inches(1.2)
section.right_margin  = Inches(1.2)


def body(text, indent=False):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(10)
    if indent:
        p.paragraph_format.first_line_indent = Inches(0.3)
    for run in p.runs:
        run.font.size = Pt(11)
    return p


# ── header block ─────────────────────────────────────────────────────────────
body("Vairamuthu M.")
body("Department of Computer Science and Engineering")
body("SRM Institute of Science and Technology, Chennai, India")
body("vm8470@srmist.edu.in")
body("")
body("August 3, 2026")
body("")
body("To the Editor-in-Chief")
body("Engineering Applications of Artificial Intelligence")
body("")

# ── body ─────────────────────────────────────────────────────────────────────
body("Dear Editor,")

body(
    "We are pleased to submit our manuscript, \"EvalBench v1 (Pilot Release): A Unified "
    "Multi-Task Benchmark for AI Evaluation in Educational Settings,\" for consideration as a "
    "research article in Engineering Applications of Artificial Intelligence.",
    indent=True,
)

body(
    "Educational AI systems for handwritten document processing are typically deployed as "
    "integrated pipelines: optical character recognition, automated grading, and confidence "
    "estimation working together, yet these capabilities are almost always evaluated in "
    "isolation by separate benchmarks (OCR-only suites such as OCRBench, grading-only suites "
    "such as EssayJudge, or general-domain multi-task suites such as GLUE and SuperGLUE that do "
    "not touch education at all). This manuscript makes the engineering case that isolated "
    "evaluation misses exactly the failure modes that matter once these components are combined: "
    "we show that two widely-used OCR models produce an Exact Match rank reversal of up to 0.589 "
    "between two standard handwriting corpora, meaning a system validated on one corpus and "
    "deployed against the other would receive a directly contradictory recommendation, and we "
    "show separately that a large language model can generate fluent, well-cited grading "
    "justifications while its stated confidence carries almost no information about whether the "
    "grade itself is correct (AUROC = 0.571, near chance). Neither finding would be visible under "
    "single-task, single-corpus evaluation, which is the gap EvalBench is built to close.",
    indent=True,
)

body(
    "EvalBench v1 contributes a public, quality-filtered corpus of 132,891 records drawn from "
    "six independent sources, a common JSON schema and fixed 70/10/20 split protocol spanning "
    "five evaluation tracks (OCR, document understanding, educational assessment, multimodal "
    "understanding, and trustworthiness), and a reproducible evaluation harness with statistically "
    "supported results, including bootstrap confidence intervals and permutation tests, for the "
    "three tracks reported in this pilot release. We believe this combination of unified benchmark "
    "infrastructure, cross-task evaluation, and deployment-oriented engineering analysis fits "
    "squarely within the scope of Engineering Applications of Artificial Intelligence, and is "
    "consistent with the journal's emphasis on AI methods validated against real engineering "
    "problems rather than on isolated algorithmic novelty.",
    indent=True,
)

body(
    "We confirm that this manuscript is original, has not been published previously, and is not "
    "under consideration for publication elsewhere, in whole or in part. All authors have "
    "reviewed and approved the submitted manuscript and agree to its submission to this journal. "
    "The authors have no competing financial or non-financial interests to declare, and no author "
    "currently serves or has previously served in an editorial capacity for this journal.",
    indent=True,
)

body(
    "We thank you and the reviewers for your time and consideration, and look forward to your "
    "response.",
    indent=True,
)

body("Sincerely,")
body("Vairamuthu M. and Sudhan M. B.")
body("On behalf of all authors")

doc.save(str(OUT_PATH))
print(f"Saved: {OUT_PATH}")
