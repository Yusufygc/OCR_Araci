from typing import Optional, Union
import numpy as np
from PIL import Image
from PySide6.QtCore import QThread, Signal
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.strategies.scan_strategy_interface import IScanStrategy


class OCRWorkerThread(QThread):
    """
    Asynchronous Qt Worker Thread for OCR processing.
    Prevents UI thread freezing during heavy AI/CV computations.
    Supports pluggable IScanStrategy scanning modes.
    """
    result_ready = Signal(OCRResult)
    error_occurred = Signal(str)

    def __init__(
        self,
        engine: IOCREngine,
        image: Union[str, np.ndarray, Image.Image],
        lang: str = "tur+eng",
        strategy: Optional[IScanStrategy] = None,
        parent=None
    ):
        super().__init__(parent)
        self._engine = engine
        self._image = image
        self._lang = lang
        self._strategy = strategy

    def run(self):
        try:
            if self._strategy is not None:
                res = self._strategy.execute(self._image, self._engine, lang=self._lang)
            else:
                res = self._engine.extract_text(self._image, lang=self._lang)

            if not self.isInterruptionRequested():
                self.result_ready.emit(res)
        except Exception as e:
            if not self.isInterruptionRequested():
                self.error_occurred.emit(str(e))

