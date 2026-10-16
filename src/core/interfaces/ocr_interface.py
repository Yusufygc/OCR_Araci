from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Union, List, Dict, Any
import numpy as np
from PIL import Image


@dataclass
class OCRResult:
    """Dataclass holding OCR extraction output cleanly."""
    text: str = ""
    confidence: float = 0.0
    processing_time: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error_message: str = ""


class IOCREngine(ABC):
    """
    Abstract Base Class for OCR Engines (Strategy Pattern).
    Enables loose coupling and easy addition of new OCR engines.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns readable name of the engine."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the engine dependencies/binaries are available on system."""
        pass

    @abstractmethod
    def extract_text(self, image: Union[str, np.ndarray, Image.Image], lang: str = "tur+eng") -> OCRResult:
        """
        Extracts text from given image input.
        
        :param image: File path, OpenCV numpy array, or PIL Image.
        :param lang: Language specification string (e.g. 'tur', 'eng', 'tur+eng').
        :return: OCRResult dataclass.
        """
        pass
