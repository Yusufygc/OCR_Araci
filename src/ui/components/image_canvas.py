import logging
import cv2
import numpy as np
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from typing import Optional

logger = logging.getLogger(__name__)


class InteractiveCropRect(QGraphicsRectItem):
    """Resizable & draggable crop rectangle overlay on graphics scene."""
    def __init__(self, rect=QRectF(), parent=None):
        super().__init__(rect, parent)
        pen = QPen(QColor(0, 230, 118), 2, Qt.DashLine)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(0, 230, 118, 40)))
        self.setFlags(
            QGraphicsRectItem.ItemIsSelectable |
            QGraphicsRectItem.ItemIsMovable |
            QGraphicsRectItem.ItemSendsGeometryChanges
        )


class ImageCanvas(QGraphicsView):
    """
    High-performance QGraphicsView image canvas.
    Supports Drag & Drop, Zoom/Pan, ROI Cropping, and OpenCV matrix rendering.
    """
    image_loaded = Signal(np.ndarray)
    roi_selected = Signal(tuple)  # (x, y, w, h)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        self._pixmap_item: Optional[QGraphicsPixmapItem] = None
        self._crop_item: Optional[InteractiveCropRect] = None
        self._current_cv_image: Optional[np.ndarray] = None
        
        self._is_selecting = False
        self._select_start = QPointF()

        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def set_cv_image(self, cv_img: np.ndarray, reset_crop: bool = True):
        """Displays OpenCV BGR or Grayscale image on canvas."""
        self._current_cv_image = cv_img.copy()
        
        if len(cv_img.shape) == 2:
            h, w = cv_img.shape
            q_img = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
        else:
            h, w, c = cv_img.shape
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_img.data, w, h, c * w, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_img)
        
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(0, 0, w, h)
        
        if reset_crop:
            self.clear_crop()
        else:
            self.restore_crop()

        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

    def get_cropped_cv_image(self) -> Optional[np.ndarray]:
        """Returns cropped OpenCV region if ROI exists, otherwise full image."""
        if self._current_cv_image is None:
            return None
        
        if self._crop_item and self._crop_item.isVisible():
            rect = self._crop_item.rect().normalized()
            pos = self._crop_item.pos()
            x = int(rect.x() + pos.x())
            y = int(rect.y() + pos.y())
            w = int(rect.width())
            h = int(rect.height())

            h_img, w_img = self._current_cv_image.shape[:2]
            x1 = max(0, min(x, w_img))
            y1 = max(0, min(y, h_img))
            x2 = max(x1 + 5, min(x + w, w_img))
            y2 = max(y1 + 5, min(y + h, h_img))

            return self._current_cv_image[y1:y2, x1:x2].copy()
        
        return self._current_cv_image.copy()

    def clear_crop(self):
        """Clears crop selection overlay."""
        if self._crop_item:
            self._scene.removeItem(self._crop_item)
            self._crop_item = None

    def restore_crop(self):
        pass

    # --- Mouse & Drag Drop Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._pixmap_item and not self.itemAt(event.pos()) == self._crop_item:
            scene_pos = self.mapToScene(event.pos())
            if self._scene.sceneRect().contains(scene_pos):
                self._is_selecting = True
                self._select_start = scene_pos
                self.clear_crop()
                self._crop_item = InteractiveCropRect(QRectF(scene_pos, scene_pos))
                self._scene.addItem(self._crop_item)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_selecting and self._crop_item:
            scene_pos = self.mapToScene(event.pos())
            rect = QRectF(self._select_start, scene_pos).normalized()
            self._crop_item.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_selecting:
            self._is_selecting = False
            if self._crop_item and (self._crop_item.rect().width() < 10 or self._crop_item.rect().height() < 10):
                self.clear_crop()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Zoom in / Zoom out via Control + Mouse Wheel."""
        if event.modifiers() & Qt.ControlModifier:
            zoom_in_factor = 1.15
            zoom_out_factor = 1 / zoom_in_factor
            if event.angleDelta().y() > 0:
                self.scale(zoom_in_factor, zoom_in_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)
        else:
            super().wheelEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff')):
                try:
                    from src.core.processing.image_processor import ImageProcessor
                    img = ImageProcessor.load_image(file_path)
                    self.set_cv_image(img)
                    self.image_loaded.emit(img)
                except Exception as e:
                    logger.warning("Sürüklenen görsel yüklenirken hata oluştu (%s): %s", file_path, e)
