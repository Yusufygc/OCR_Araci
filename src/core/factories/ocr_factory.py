from typing import Dict, Type, List
from src.core.interfaces.ocr_interface import IOCREngine
from src.core.engines.easyocr_engine import EasyOCREngine
from src.core.engines.tesseract_engine import TesseractEngine


class OCREngineFactory:
    """
    Factory Pattern for OCR Engines.
    Provides decoupled instantiation and discovery of available OCR engines.
    """

    _registry: Dict[str, Type[IOCREngine]] = {
        "easyocr": EasyOCREngine,
        "tesseract": TesseractEngine,
    }
    _instances: Dict[str, IOCREngine] = {}

    @classmethod
    def register_engine(cls, key: str, engine_cls: Type[IOCREngine]) -> None:
        """Allows dynamic registration of new OCR engine strategies at runtime."""
        cls._registry[key] = engine_cls
        cls._instances.pop(key, None)

    @classmethod
    def get_engine(cls, key: str, **kwargs) -> IOCREngine:
        """Returns a cached or newly instantiated OCR engine strategy."""
        if key not in cls._registry:
            raise ValueError(f"Unknown OCR engine key: '{key}'. Available: {list(cls._registry.keys())}")
        if kwargs:
            return cls._registry[key](**kwargs)
        if key not in cls._instances:
            cls._instances[key] = cls._registry[key]()
        return cls._instances[key]

    @classmethod
    def list_available_engines(cls) -> List[Dict[str, str]]:
        """Returns a list of registered engines and their availability state."""
        available = []
        for key in cls._registry:
            instance = cls.get_engine(key)
            available.append({
                "id": key,
                "name": instance.name,
                "available": instance.is_available
            })
        return available
