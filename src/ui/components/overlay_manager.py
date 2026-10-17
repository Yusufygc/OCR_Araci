from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsView

BORDER_COLOR_RGB = (0, 230, 118)
NORMAL_ALPHA = 25
HOVER_ALPHA = 80
BORDER_WIDTH = 2
MIN_BOX_DIMENSION = 2.0


class ClickableBoxItem(QGraphicsRectItem):
    """Interactive bounding box overlay on image canvas with hover effects and click-to-copy."""

    def __init__(
        self,
        rect: QRectF,
        text: str,
        confidence: float,
        on_click_callback: Optional[Callable[[str], None]] = None,
        parent=None
    ):
        super().__init__(rect, parent)
        self._text = text
        self._confidence = confidence
        self._callback = on_click_callback

        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"{text}\nGüven: %{confidence * 100:.1f}\n(Kopyalamak için tıklayın)")

        self._normal_pen = QPen(QColor(*BORDER_COLOR_RGB, 180), BORDER_WIDTH)
        self._normal_brush = QBrush(QColor(*BORDER_COLOR_RGB, NORMAL_ALPHA))
        self._hover_pen = QPen(QColor(255, 255, 255), BORDER_WIDTH)
        self._hover_brush = QBrush(QColor(*BORDER_COLOR_RGB, HOVER_ALPHA))

        self.setPen(self._normal_pen)
        self.setBrush(self._normal_brush)

    def hoverEnterEvent(self, event):
        self.setPen(self._hover_pen)
        self.setBrush(self._hover_brush)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self._normal_pen)
        self.setBrush(self._normal_brush)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._text.strip():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self._text.strip())
            if self._callback:
                self._callback(self._text.strip())
        super().mousePressEvent(event)


class CanvasOverlayManager(QObject):
    """
    Pluggable Overlay Manager for Interactive Bounding Box Overlays.
    Decoupled from ImageCanvas core logic; attaches dynamically to any QGraphicsScene.
    """
    box_clicked = Signal(str)

    def __init__(self, canvas: QGraphicsView, parent=None):
        super().__init__(parent)
        self._canvas = canvas
        self._items: List[ClickableBoxItem] = []
        self._is_enabled = True

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    def set_enabled(self, enabled: bool):
        """Enables or disables interactive bounding box visualization."""
        self._is_enabled = enabled
        self.set_visible(enabled)

    def set_visible(self, visible: bool):
        """Toggles visibility of existing bounding box overlays."""
        for item in self._items:
            item.setVisible(visible and self._is_enabled)

    def clear(self):
        """Removes all bounding box overlays from the canvas scene cleanly."""
        scene = self._canvas.scene()
        if scene:
            for item in self._items:
                try:
                    if item.scene() is scene:
                        scene.removeItem(item)
                except RuntimeError:
                    # QGraphicsScene.clear() (yeni görsel yüklenince) öğelerin C++ nesnesini zaten sildi.
                    continue
        self._items.clear()

    def render_boxes(self, details: List[Dict[str, Any]]):
        """
        Draws clickable, translucent bounding boxes over detected words/phrases.
        :param details: List of detected items with 'bbox', 'text', 'confidence'.
        """
        self.clear()
        scene = self._canvas.scene()
        if not scene or not self._is_enabled or not details:
            return

        for d in details:
            text = str(d.get("text", "")).strip()
            conf = float(d.get("confidence", 0.0))
            bbox = d.get("bbox", [])
            if not text or len(bbox) < 4:
                continue

            xs = [float(pt[0]) for pt in bbox]
            ys = [float(pt[1]) for pt in bbox]
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            w = max(MIN_BOX_DIMENSION, x2 - x1)
            h = max(MIN_BOX_DIMENSION, y2 - y1)

            rect = QRectF(x1, y1, w, h)
            item = ClickableBoxItem(
                rect, text, conf, on_click_callback=self.box_clicked.emit
            )
            scene.addItem(item)
            self._items.append(item)
