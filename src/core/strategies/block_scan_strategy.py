from typing import Any, Union
import numpy as np
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.strategies.scan_strategy_interface import IScanStrategy
from src.core.layout.xy_cut_analyzer import XYCutLayoutAnalyzer
from src.core.processing.image_processor import ImageProcessor


class BlockScanStrategy(IScanStrategy):
    """
    2D Block and Column-Aware regional scanning strategy.
    Separates independent cards, diagram nodes, and multi-column articles using spatial clustering.
    """

    def __init__(self, analyzer: Any = None):
        self._analyzer = analyzer or XYCutLayoutAnalyzer()

    @property
    def mode_id(self) -> str:
        return "block"

    @property
    def display_name(self) -> str:
        return "Bölgesel / Şema (Blok Blok)"

    def execute(
        self,
        image: Union[str, np.ndarray, Image.Image],
        engine: IOCREngine,
        lang: str = "tur+eng",
        **kwargs: Any
    ) -> OCRResult:
        cv_img = ImageProcessor.load_image(image)
        raw_res = engine.extract_text(cv_img, lang=lang)
        if not raw_res.success or not raw_res.details:
            return raw_res

        layout_res = self._analyzer.analyze(raw_res.details, cv_img.shape[:2])
        if not layout_res.full_text.strip():
            return raw_res

        return OCRResult(
            text=layout_res.full_text,
            confidence=layout_res.confidence if layout_res.confidence > 0 else raw_res.confidence,
            processing_time=raw_res.processing_time,
            details=raw_res.details,
            success=True
        )
