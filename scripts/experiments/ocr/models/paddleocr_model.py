"""PaddleOCR wrapper (CPU/GPU)."""

from __future__ import annotations
from pathlib import Path
from .base import OCRModel


class PaddleOCRModel(OCRModel):
    name = "paddleocr"

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        self.lang    = lang
        self.use_gpu = use_gpu
        self._ocr    = None

    def load(self) -> None:
        from paddleocr import PaddleOCR
        self._ocr = PaddleOCR(lang=self.lang)

    def predict(self, image_path: Path) -> str:
        result = self._ocr.predict(str(image_path))
        if not result:
            return ""
        # PaddleOCR v3 returns list of dicts with 'rec_texts' key
        item = result[0]
        if isinstance(item, dict):
            texts = item.get("rec_texts", [])
            return " ".join(t for t in texts if t).strip()
        # fallback for older API: list of [[box, (text, conf)], ...]
        if isinstance(item, list):
            lines = []
            for line in item:
                if line and len(line) >= 2 and line[1]:
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                    lines.append(text)
            return " ".join(lines).strip()
        return ""

    def unload(self) -> None:
        del self._ocr
        self._ocr = None
