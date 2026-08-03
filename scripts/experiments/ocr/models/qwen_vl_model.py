"""Qwen2.5-VL OCR wrapper — via Hugging Face transformers."""

from __future__ import annotations
from pathlib import Path
from PIL import Image
from .base import OCRModel

OCR_PROMPT = (
    "Please transcribe ALL the handwritten text in this image exactly as written. "
    "Output ONLY the transcribed text with no commentary, no explanations, "
    "no quotation marks, no formatting — just the raw text."
)


class QwenVLModel(OCRModel):
    def __init__(self, variant: str = "Qwen/Qwen2.5-VL-7B-Instruct"):
        self.name      = "qwen2_5_vl"
        self._model_id = variant
        self._model    = None
        self._processor = None
        self._device   = None

    def load(self) -> None:
        import torch
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        if torch.cuda.is_available():
            self._device = "cuda"
        elif torch.backends.mps.is_available():
            self._device = "mps"
        else:
            self._device = "cpu"
        print(f"  [{self.name}] loading on {self._device} (this may take a few minutes) ...")
        self._processor = AutoProcessor.from_pretrained(self._model_id)
        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self._model_id, torch_dtype="auto",
        ).to(self._device)
        self._model.eval()

    def predict(self, image_path: Path) -> str:
        import torch
        from qwen_vl_utils import process_vision_info
        img = Image.open(image_path).convert("RGB")
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text",  "text": OCR_PROMPT},
            ],
        }]
        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt",
        ).to(self._device)
        with torch.no_grad():
            generated_ids = self._model.generate(**inputs, max_new_tokens=256)
        generated_ids_trimmed = [
            out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)
        ]
        return self._processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()

    def unload(self) -> None:
        import torch
        del self._model, self._processor
        self._model = self._processor = None
        if self._device == "cuda":
            torch.cuda.empty_cache()
        elif self._device == "mps":
            torch.mps.empty_cache()
