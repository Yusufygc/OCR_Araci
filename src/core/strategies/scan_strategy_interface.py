from abc import ABC, abstractmethod
from typing import Any, Union
import numpy as np
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult


class IScanStrategy(ABC):
    """
    Pluggable Strategy Contract for OCR Scanning Modes.
    Allows dynamic swapping between Line-by-Line, Block/Regional, and Interactive Multi-Region modes.
    """

    @property
    @abstractmethod
    def mode_id(self) -> str:
        """Unique strategy identifier (e.g., 'line', 'block', 'multi_region')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable display name for UI dropdowns."""
        pass

    @abstractmethod
    def execute(
        self,
        image: Union[str, np.ndarray, Image.Image],
        engine: IOCREngine,
        lang: str = "tur+eng",
        **kwargs: Any
    ) -> OCRResult:
        """
        Executes the scanning strategy using the provided OCR engine and optional parameters.
        :param image: Input image.
        :param engine: Configured IOCREngine instance.
        :param lang: Language code string.
        :param kwargs: Additional strategy parameters (e.g. selected regions).
        :return: Structured OCRResult.
        """
        pass
