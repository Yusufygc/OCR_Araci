import numpy as np
from PySide6.QtCore import QThread, Signal
from typing import Union
from PIL import Image
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult


class OCRWorkerThread(QThread):
    """
    Asynchronous Qt Worker Thread for OCR processing.
    Prevents UI thread freezing during heavy AI/CV computations.
    """
    result_ready = Signal(OCRResult)
    error_occurred = Signal(str)

    def __init__(self, engine: IOCREngine, image: Union[str, np.ndarray, Image.Image], lang: str = "tur+eng", parent=None):
        super().__init__(parent)
        self._engine = engine
        self._image = image
        self._lang = lang

    def run(self):
        try:
            res = self._engine.extract_text(self._image, lang=self._lang)
            if not self.isInterruptionRequested():
                self.result_ready.emit(res)
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error_occurred.emit(str(e))
