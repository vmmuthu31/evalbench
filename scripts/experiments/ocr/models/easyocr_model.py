"""EasyOCR wrapper (CPU / MPS via CUDA flag)."""

from __future__ import annotations
from pathlib import Path
from .base import OCRModel


class EasyOCRModel(OCRModel):
    name = "easyocr"

    def __init__(self, gpu: bool = False):
        self.gpu = gpu
        self._reader = None

    def load(self) -> None:
        import easyocr
        self._reader = easyocr.Reader(["en"], gpu=self.gpu, verbose=False)

    def predict(self, image_path: Path) -> str:
        results = self._reader.readtext(str(image_path), detail=0, paragraph=True)
        return " ".join(results).strip()

    def unload(self) -> None:
        del self._reader
        self._reader = None
