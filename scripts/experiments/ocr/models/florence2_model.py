"""Florence-2 OCR wrapper (microsoft/Florence-2-base or large)."""

from __future__ import annotations
from pathlib import Path
from PIL import Image
from .base import OCRModel


class Florence2Model(OCRModel):
    def __init__(self, variant: str = "base"):
        self.variant   = variant
        self.name      = f"florence2_{variant}"
        self._model_id = f"microsoft/Florence-2-{variant}"
        self._model    = None
        self._processor = None
        self._device   = None

    def load(self) -> None:
        import torch
        from transformers import AutoProcessor, AutoModelForCausalLM
        if torch.backends.mps.is_available():
            self._device = "mps"
        elif torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
        print(f"  [{self.name}] loading on {self._device} ...")
        self._processor = AutoProcessor.from_pretrained(
            self._model_id, trust_remote_code=True)
        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_id, trust_remote_code=True).to(self._device)
        self._model.eval()

    def predict(self, image_path: Path) -> str:
        import torch
        img    = Image.open(image_path).convert("RGB")
        task   = "<OCR>"
        inputs = self._processor(text=task, images=img, return_tensors="pt").to(self._device)
        with torch.no_grad():
            generated_ids = self._model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=512,
                num_beams=3,
            )
        result = self._processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed = self._processor.post_process_generation(
            result, task=task, image_size=(img.width, img.height))
        return parsed.get("<OCR>", "").strip()

    def unload(self) -> None:
        import torch
        del self._model, self._processor
        self._model = self._processor = None
        if self._device == "mps":
            torch.mps.empty_cache()
        elif self._device == "cuda":
            torch.cuda.empty_cache()
