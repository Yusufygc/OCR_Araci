import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.strategies.scan_strategy_interface import IScanStrategy
from src.core.processing.image_processor import ImageProcessor


class MultiRegionStrategy(IScanStrategy):
    """
    Interactive Multi-Region Scanning Strategy.
    Scans explicitly selected user regions in sequential order and aggregates outputs.
    """

    def __init__(self, regions: Optional[List[Tuple[int, int, int, int]]] = None):
        self._regions: List[Tuple[int, int, int, int]] = list(regions) if regions else []

    def set_regions(self, regions: List[Tuple[int, int, int, int]]):
        """Sets target ROI regions to scan in sequence."""
        self._regions = list(regions)

    @property
    def mode_id(self) -> str:
        return "multi_region"

    @property
    def display_name(self) -> str:
        return "Seçili Alanlar (Çoklu Bölge)"

    @staticmethod
    def _shift_details(details: List[Dict[str, Any]], offset_x: int, offset_y: int) -> List[Dict[str, Any]]:
        """Offsets crop bounding box coordinates back to canvas root space."""
        return ImageProcessor.shift_details_coordinates(details, offset_x, offset_y)

    def execute(
        self,
        image: Union[str, np.ndarray, Image.Image],
        engine: IOCREngine,
        lang: str = "tur+eng",
        **kwargs: Any
    ) -> OCRResult:
        regions: List[Tuple[int, int, int, int]] = kwargs.get("regions") or self._regions
        if not regions:
            return engine.extract_text(image, lang=lang)

        start_time = time.time()
        cv_img = ImageProcessor.load_image(image)
        section_texts = []
        all_details = []
        confs = []

        for idx, (x, y, w, h) in enumerate(regions, start=1):
            crop = ImageProcessor.crop_roi(cv_img, int(x), int(y), int(w), int(h))
            if crop.size == 0:
                continue
            crop_res = engine.extract_text(crop, lang=lang)
            if crop_res.text.strip():
                section_texts.append(f"[{idx}. Seçili Bölge]\n{crop_res.text.strip()}")
                confs.append(crop_res.confidence)
                all_details.extend(self._shift_details(crop_res.details, int(x), int(y)))

        full_text = "\n\n".join(section_texts)
        avg_conf = (sum(confs) / len(confs)) if confs else 0.0
        elapsed = time.time() - start_time

        return OCRResult(
            text=full_text,
            confidence=avg_conf,
            processing_time=elapsed,
            details=all_details,
            success=True
        )
