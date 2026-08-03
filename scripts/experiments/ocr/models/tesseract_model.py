"""Tesseract 5 OCR wrapper (CPU, no model download needed)."""

from __future__ import annotations
from pathlib import Path
from PIL import Image
import pytesseract
from .base import OCRModel


class TesseractModel(OCRModel):
    name = "tesseract5"

    def __init__(self, lang: str = "eng", psm: int = 7):
        # psm 7 = single line (good for word-level IAM); psm 6 for page/paragraph
        self.lang = lang
        self.config = f"--oem 3 --psm {psm}"

    def load(self) -> None:
        # verify tesseract is accessible
        pytesseract.get_tesseract_version()

    def predict(self, image_path: Path) -> str:
        img = Image.open(image_path).convert("RGB")
        text = pytesseract.image_to_string(img, lang=self.lang, config=self.config)
        return text.strip()

    def unload(self) -> None:
        pass
