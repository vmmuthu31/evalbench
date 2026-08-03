"""TrOCR wrapper (microsoft/trocr-base-handwritten or large)."""

from __future__ import annotations
from pathlib import Path
from PIL import Image
from .base import OCRModel


class TrOCRModel(OCRModel):
    def __init__(self, variant: str = "base"):
        # variant: "base" or "large"
        self.variant = variant
        self.name = f"trocr_{variant}"
        self._model_id = f"microsoft/trocr-{variant}-handwritten"
        self._processor = None
        self._model = None
        self._device = None

    def load(self) -> None:
        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        if torch.backends.mps.is_available():
            self._device = "mps"
        elif torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
        print(f"  [{self.name}] loading on {self._device} ...")
        self._processor = TrOCRProcessor.from_pretrained(self._model_id)
        self._model = VisionEncoderDecoderModel.from_pretrained(self._model_id).to(self._device)
        self._model.eval()

    def predict(self, image_path: Path) -> str:
        import torch
        img = Image.open(image_path).convert("RGB")
        pixel_values = self._processor(images=img, return_tensors="pt").pixel_values.to(self._device)
        with torch.no_grad():
            generated_ids = self._model.generate(pixel_values)
        return self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

    def unload(self) -> None:
        import torch
        del self._model, self._processor
        self._model = self._processor = None
        if self._device == "mps":
            torch.mps.empty_cache()
        elif self._device == "cuda":
            torch.cuda.empty_cache()
