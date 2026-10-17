from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class TextBlock:
    """Represents a coherent 2D visual block of text (e.g. card, diagram box, or column)."""
    block_id: int
    bbox: Tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max)
    lines: List[str] = field(default_factory=list)
    text: str = ""
    confidence: float = 0.0
    word_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RegionAnalysisResult:
    """Contains grouped text blocks and combined hierarchical reading output."""
    blocks: List[TextBlock] = field(default_factory=list)
    full_text: str = ""
    confidence: float = 0.0


class ILayoutAnalyzer(ABC):
    """
    Contract for Layout Analysis and Reading Order strategies.
    Decouples raw OCR word/box detections from 2D spatial arrangement.
    """

    @abstractmethod
    def analyze(
        self,
        word_boxes: List[Dict[str, Any]],
        image_shape: Tuple[int, int]
    ) -> RegionAnalysisResult:
        """
        Analyzes bounding boxes and clusters them into distinct, structured blocks.
        :param word_boxes: List of dicts with 'bbox', 'text', 'confidence'.
        :param image_shape: (height, width) of the source image.
        :return: RegionAnalysisResult with ordered TextBlocks and formatted text.
        """
        pass
