import logging
import cv2
import numpy as np
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

MIN_SELECTION_DIM = 10
CROP_PADDING_PX = 5
ZOOM_IN_FACTOR = 1.15


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
        self._crop_items: List[InteractiveCropRect] = []
        self._current_cv_image: Optional[np.ndarray] = None

        self._is_selecting = False
        self._select_start = QPointF()

        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    @property
    def _crop_item(self) -> Optional[InteractiveCropRect]:
        """Backward-compatible accessor for primary crop rectangle."""
        return self._crop_items[0] if self._crop_items else None

    @_crop_item.setter
    def _crop_item(self, item: Optional[InteractiveCropRect]):
        if item is None:
            self._crop_items.clear()
        else:
            self._crop_items = [item]

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

    def get_selected_regions(self) -> List[Tuple[int, int, int, int]]:
        """Returns list of normalized (x, y, w, h) bounding boxes in image coordinate space."""
        if self._current_cv_image is None or not self._crop_items:
            return []

        h_img, w_img = self._current_cv_image.shape[:2]
        regions: List[Tuple[int, int, int, int]] = []
        for item in self._crop_items:
            if not item.isVisible():
                continue
            rect = item.rect().normalized()
            pos = item.pos()
            x = int(rect.x() + pos.x())
            y = int(rect.y() + pos.y())
            w = int(rect.width())
            h = int(rect.height())

            x1 = max(0, min(x, w_img))
            y1 = max(0, min(y, h_img))
            x2 = max(x1 + CROP_PADDING_PX, min(x + w, w_img))
            y2 = max(y1 + CROP_PADDING_PX, min(y + h, h_img))
            regions.append((x1, y1, x2 - x1, y2 - y1))
        return regions

    def get_cropped_cv_image(self) -> Optional[np.ndarray]:
        """Returns cropped OpenCV region if ROI exists, otherwise full image copy."""
        if self._current_cv_image is None:
            return None
        regions = self.get_selected_regions()
        if regions:
            x, y, w, h = regions[0]
            return self._current_cv_image[y:y + h, x:x + w].copy()
        return self._current_cv_image.copy()

    def get_full_cv_image(self) -> Optional[np.ndarray]:
        """Returns a copy of the whole displayed OpenCV image, ignoring any ROI selection."""
        if self._current_cv_image is None:
            return None
        return self._current_cv_image.copy()

    def get_primary_region_offset(self) -> Tuple[int, int]:
        """Returns top-left (x, y) of the first ROI used by get_cropped_cv_image(), or (0, 0) without ROI."""
        regions = self.get_selected_regions()
        return (regions[0][0], regions[0][1]) if regions else (0, 0)

    def clear_crop(self):
        """Clears all active crop selection overlays from canvas scene."""
        for item in self._crop_items:
            if item.scene() == self._scene:
                self._scene.removeItem(item)
        self._crop_items.clear()

    def restore_crop(self):
        pass

    # --- Mouse & Drag Drop Events ---
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is not None and item != self._pixmap_item and item not in self._crop_items:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.RightButton:
            self.clear_crop()
            return

        if event.button() == Qt.LeftButton and self._pixmap_item and item not in self._crop_items:
            scene_pos = self.mapToScene(event.pos())
            if self._scene.sceneRect().contains(scene_pos):
                self._is_selecting = True
                self._select_start = scene_pos
                if not (event.modifiers() & Qt.ShiftModifier):
                    self.clear_crop()
                crop = InteractiveCropRect(QRectF(scene_pos, scene_pos))
                self._crop_items.append(crop)
                self._scene.addItem(crop)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_selecting and self._crop_items:
            scene_pos = self.mapToScene(event.pos())
            rect = QRectF(self._select_start, scene_pos).normalized()
            self._crop_items[-1].setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._is_selecting:
            self._is_selecting = False
            if self._crop_items:
                last_crop = self._crop_items[-1]
                if last_crop.rect().width() < MIN_SELECTION_DIM or last_crop.rect().height() < MIN_SELECTION_DIM:
                    if last_crop.scene() == self._scene:
                        self._scene.removeItem(last_crop)
                    self._crop_items.pop()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Zoom in / Zoom out via Control + Mouse Wheel."""
        if event.modifiers() & Qt.ControlModifier:
            zoom_out_factor = 1.0 / ZOOM_IN_FACTOR
            if event.angleDelta().y() > 0:
                self.scale(ZOOM_IN_FACTOR, ZOOM_IN_FACTOR)
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
