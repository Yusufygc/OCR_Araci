from typing import Any, Union
import numpy as np
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.strategies.scan_strategy_interface import IScanStrategy


class LineScanStrategy(IScanStrategy):
    """Standard sequential line-by-line reading strategy for linear books and documents."""

    @property
    def mode_id(self) -> str:
        return "line"

    @property
    def display_name(self) -> str:
        return "Düz Metin (Satır Satır)"

    def execute(
        self,
        image: Union[str, np.ndarray, Image.Image],
        engine: IOCREngine,
        lang: str = "tur+eng",
        **kwargs: Any
    ) -> OCRResult:
        return engine.extract_text(image, lang=lang)
