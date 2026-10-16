import time
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.processing.image_processor import ImageProcessor


MIN_TOKEN_GAP_PX = 4.0
CRAFT_LOW_TEXT = 0.25
CRAFT_LINK_THRESH = 0.30
CRAFT_TEXT_THRESH = 0.40
CONTRAST_THRESH = 0.10
ADJUST_CONTRAST = 0.50
LINE_HEIGHT_RATIO = 0.55
MIN_EASYOCR_PROB = 0.20
MIN_NON_ALNUM_PROB = 0.45
NO_SPACE_PUNCT = (".", "_", "/", "-", ":", "@", "#")


def _detect_gpu() -> bool:
    """Checks whether CUDA GPU acceleration is available via PyTorch."""
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


class EasyOCREngine(IOCREngine):
    """
    EasyOCR Strategy Implementation.
    Uses PyTorch deep learning model locally for multi-language OCR.
    Lazy initializes reader instance and reconstructs 2D reading order.
    """

    def __init__(self, gpu: Optional[bool] = None):
        self._gpu = _detect_gpu() if gpu is None else gpu
        self._reader: Optional[Any] = None
        self._loaded_langs: List[str] = []

    @property
    def name(self) -> str:
        return "EasyOCR (Derin Öğrenme)"

    @property
    def is_available(self) -> bool:
        try:
            __import__("easyocr")
            return True
        except ImportError:
            return False

    def _get_reader(self, lang_list: List[str]):
        import easyocr
        if self._reader is None or sorted(self._loaded_langs) != sorted(lang_list):
            self._reader = easyocr.Reader(lang_list, gpu=self._gpu, verbose=False)
            self._loaded_langs = list(lang_list)
        return self._reader

    def _parse_languages(self, lang: str) -> List[str]:
        lang_map = {'tur': 'tr', 'eng': 'en', 'deu': 'de', 'fra': 'fr', 'spa': 'es'}
        langs = []
        for part in lang.split('+'):
            part_clean = part.strip().lower()
            if part_clean:
                langs.append(lang_map.get(part_clean, part_clean))
        return langs or ['tr', 'en']

    @staticmethod
    def _box_metrics(bbox: list) -> Tuple[float, float, float, float]:
        """Returns (x_min, x_max, y_center, height) for a 4-point bounding box."""
        xs = [float(pt[0]) for pt in bbox]
        ys = [float(pt[1]) for pt in bbox]
        y_min, y_max = min(ys), max(ys)
        return min(xs), max(xs), (y_min + y_max) / 2.0, max(1.0, y_max - y_min)

    @classmethod
    def _join_line_tokens(cls, line_sorted: List[Dict[str, Any]]) -> str:
        """Joins line tokens intelligently preserving code identifiers, dots, and underscores."""
        if not line_sorted:
            return ""
        tokens = [line_sorted[0]["text"]]
        for i in range(1, len(line_sorted)):
            prev, curr = line_sorted[i - 1], line_sorted[i]
            prev_txt, curr_txt = prev["text"], curr["text"]
            gap = curr["x_min"] - prev["x_max"]
            if gap < MIN_TOKEN_GAP_PX or prev_txt.endswith(NO_SPACE_PUNCT) or curr_txt.startswith(NO_SPACE_PUNCT):
                tokens.append(curr_txt)
            else:
                tokens.append(" " + curr_txt)
        return "".join(tokens)

    @classmethod
    def _group_boxes_into_lines(cls, items: List[Dict[str, Any]]) -> List[str]:
        """Clusters detected word/phrase boxes into horizontal lines and sorts left-to-right."""
        if not items:
            return []
        sorted_by_y = sorted(items, key=lambda it: it["y_center"])
        lines: List[List[Dict[str, Any]]] = [[sorted_by_y[0]]]

        for item in sorted_by_y[1:]:
            current_line = lines[-1]
            avg_y = sum(x["y_center"] for x in current_line) / len(current_line)
            avg_h = sum(x["height"] for x in current_line) / len(current_line)
            if abs(item["y_center"] - avg_y) <= avg_h * LINE_HEIGHT_RATIO:
                current_line.append(item)
            else:
                lines.append([item])

        extracted_lines = []
        for line in lines:
            line_sorted = sorted(line, key=lambda it: it["x_min"])
            extracted_lines.append(cls._join_line_tokens(line_sorted))
        return extracted_lines

    def _format_ocr_results(self, results: list):
        total_conf = 0.0
        details = []
        annotated_items = []

        for bbox, text, prob in results:
            clean_text = str(text).strip()
            prob_val = float(prob)
            has_alnum = any(ch.isalnum() for ch in clean_text)
            if not clean_text or prob_val < MIN_EASYOCR_PROB or (not has_alnum and prob_val < MIN_NON_ALNUM_PROB):
                continue
            x_min, x_max, y_center, height = self._box_metrics(bbox)
            total_conf += prob_val
            details.append({"bbox": bbox, "text": clean_text, "confidence": prob_val})
            annotated_items.append({
                "text": clean_text, "x_min": x_min, "x_max": x_max,
                "y_center": y_center, "height": height
            })

        extracted_lines = self._group_boxes_into_lines(annotated_items)
        full_text = "\n".join(extracted_lines)
        avg_conf = (total_conf / len(details)) if details else 0.0
        return full_text, avg_conf, details

    def extract_text(self, image: Union[str, np.ndarray, Image.Image], lang: str = "tur+eng") -> OCRResult:
        if not self.is_available:
            return OCRResult(success=False, error_message="EasyOCR kütüphanesi yüklü değil.")

        start_time = time.time()
        try:
            cv_img = ImageProcessor.load_image(image)
            prepared_img = ImageProcessor.prepare_for_ocr(cv_img)
            langs = self._parse_languages(lang)
            reader = self._get_reader(langs)
            results = reader.readtext(
                prepared_img,
                low_text=CRAFT_LOW_TEXT,
                link_threshold=CRAFT_LINK_THRESH,
                text_threshold=CRAFT_TEXT_THRESH,
                contrast_ths=CONTRAST_THRESH,
                adjust_contrast=ADJUST_CONTRAST
            )

            full_text, avg_conf, details = self._format_ocr_results(results)
            elapsed = time.time() - start_time

            return OCRResult(
                text=full_text,
                confidence=avg_conf,
                processing_time=elapsed,
                details=details,
                success=True
            )
        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"EasyOCR Hatası: {str(e)}",
                processing_time=time.time() - start_time
            )
