import os
import shutil
import time
import numpy as np
from typing import Union, List
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.processing.image_processor import ImageProcessor


MIN_TESS_CONF = 25.0
SINGLE_CHAR_MIN_CONF = 88.0
PERCENT_DIVISOR = 100.0
ALLOWED_SINGLE_PUNCT = ("*", "-", "|", ">")
VALID_SINGLE_LETTERS = ("a", "o", "i")
TESSERACT_CONFIG = "--oem 3 --psm 3"


def _ensure_tesseract_configured():
    """Detects standard Tesseract-OCR binary paths if not present in system PATH."""
    try:
        import pytesseract
        if shutil.which("tesseract") is not None:
            return
        standard_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for path in standard_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    except (ImportError, OSError):
        # Tesseract veya pytesseract yüklü değilse fallback yapılamaz; is_available False dönecektir.
        pass


class TesseractEngine(IOCREngine):
    """
    PyTesseract Strategy Implementation.
    Uses Tesseract OCR binary locally with LSTM (OEM 3), automatic layout segmentation (PSM 3),
    and single-pass extraction.
    """

    @property
    def name(self) -> str:
        return "PyTesseract (Hızlı Çevrimdışı)"

    @property
    def is_available(self) -> bool:
        try:
            import pytesseract
            _ensure_tesseract_configured()
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @staticmethod
    def _join_tesseract_line(words: List[str]) -> str:
        """Joins words in a line avoiding unnatural spaces around dots, underscores, or slashes."""
        if not words:
            return ""
        tokens = [words[0]]
        no_space = (".", "_", "/", "-", ":")
        for i in range(1, len(words)):
            prev, curr = words[i - 1], words[i]
            if prev.endswith(no_space) or curr.startswith(no_space):
                tokens.append(curr)
            else:
                tokens.append(" " + curr)
        return "".join(tokens)

    @staticmethod
    def _is_low_conf_noise(word: str, conf_val: float) -> bool:
        """Checks whether a single word token is low-confidence symbol or icon noise."""
        if conf_val < MIN_TESS_CONF:
            return True
        if word in ALLOWED_SINGLE_PUNCT:
            return False
        if not any(ch.isalnum() for ch in word):
            return True
        return len(word) == 1 and word.isalpha() and word.lower() not in VALID_SINGLE_LETTERS and conf_val < SINGLE_CHAR_MIN_CONF

    @classmethod
    def _is_stray_glyph(cls, word: str, conf_val: float, i: int, texts: List[str]) -> bool:
        """Detects low-confidence UI icon garbage or stray glyphs preceding identifiers."""
        if cls._is_low_conf_noise(word, conf_val):
            return True
        if word in ("#&", "@", "&", "©") and i + 1 < len(texts):
            nxt = str(texts[i + 1]).strip()
            return bool(nxt and ('.' in nxt or '_' in nxt or nxt[0].isupper()))
        return False

    @classmethod
    def _parse_tesseract_data(cls, data: dict):
        """Extracts structured lines, average confidence, and word details from image_to_data dict."""
        texts = data.get("text", [])
        confs = data.get("conf", [])
        blocks = data.get("block_num", [0] * len(texts))
        pars = data.get("par_num", [0] * len(texts))
        lines = data.get("line_num", [0] * len(texts))
        lefts, tops = data.get("left", [0] * len(texts)), data.get("top", [0] * len(texts))
        widths, heights = data.get("width", [0] * len(texts)), data.get("height", [0] * len(texts))

        line_groups, confidences, details = {}, [], []
        for i, raw_word in enumerate(texts):
            word = str(raw_word).strip()
            conf_val = float(confs[i]) if i < len(confs) and str(confs[i]) != "-1" else -1.0
            if not word or cls._is_stray_glyph(word, conf_val, i, texts):
                continue

            confidences.append(conf_val)
            line_groups.setdefault((blocks[i], pars[i], lines[i]), []).append(word)
            x, y, w, h = int(lefts[i]), int(tops[i]), int(widths[i]), int(heights[i])
            details.append({
                "bbox": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                "text": word,
                "confidence": conf_val / PERCENT_DIVISOR
            })

        full_text = "\n".join(cls._join_tesseract_line(w) for w in line_groups.values())
        avg_conf = (sum(confidences) / len(confidences) / PERCENT_DIVISOR) if confidences else 0.0
        return full_text, avg_conf, details

    def extract_text(self, image: Union[str, np.ndarray, Image.Image], lang: str = "tur+eng") -> OCRResult:
        try:
            import pytesseract
            _ensure_tesseract_configured()
        except ImportError:
            return OCRResult(success=False, error_message="pytesseract kütüphanesi yüklü değil.")

        start_time = time.time()
        try:
            cv_img = ImageProcessor.load_image(image)
            prepared_img, scale, pad = ImageProcessor.prepare_for_ocr_with_transform(cv_img)
            gray = ImageProcessor.to_grayscale(prepared_img)
            pil_img = Image.fromarray(gray)

            data = pytesseract.image_to_data(
                pil_img, lang=lang, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT
            )
            full_text, avg_conf, details = self._parse_tesseract_data(data)
            details = ImageProcessor.restore_details_coordinates(details, scale, pad)
            elapsed = time.time() - start_time

            return OCRResult(
                text=full_text.strip(),
                confidence=avg_conf,
                processing_time=elapsed,
                details=details,
                success=True
            )

        except Exception as e:
            return OCRResult(
                success=False,
                error_message=f"Tesseract Hatası (Tesseract sistemde yüklü mü?): {str(e)}",
                processing_time=time.time() - start_time
            )
