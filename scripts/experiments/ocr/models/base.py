"""Abstract base class for all OCR model wrappers."""

from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image


class OCRModel(ABC):
    name: str = "base"

    @abstractmethod
    def load(self) -> None:
        """Load model weights into memory. Called once before evaluation."""

    @abstractmethod
    def predict(self, image_path: Path) -> str:
        """Return OCR text for a single image."""

    def unload(self) -> None:
        """Optional: release GPU/CPU memory after evaluation."""
