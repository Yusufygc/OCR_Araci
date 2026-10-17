import unittest
from PySide6.QtWidgets import QApplication
from src.ui.components.image_canvas import ImageCanvas
from src.ui.components.overlay_manager import CanvasOverlayManager


class TestOverlayManager(unittest.TestCase):
    """Unit tests for CanvasOverlayManager bounding box visualization."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.canvas = ImageCanvas()
        self.overlay = CanvasOverlayManager(self.canvas)

    def test_render_and_clear_boxes(self):
        sample_details = [
            {
                "text": "Deneme",
                "confidence": 0.95,
                "bbox": [[10, 10], [50, 10], [50, 30], [10, 30]]
            },
            {
                "text": "İkinci",
                "confidence": 0.88,
                "bbox": [[60, 10], [100, 10], [100, 30], [60, 30]]
            }
        ]
        self.overlay.render_boxes(sample_details)
        self.assertEqual(len(self.overlay._items), 2)

        self.overlay.clear()
        self.assertEqual(len(self.overlay._items), 0)

    def test_visibility_and_enabled(self):
        sample_details = [
            {
                "text": "Metin",
                "confidence": 0.90,
                "bbox": [[10, 10], [40, 10], [40, 25], [10, 25]]
            }
        ]
        self.overlay.render_boxes(sample_details)
        self.assertTrue(self.overlay.is_enabled)

        self.overlay.set_enabled(False)
        self.assertFalse(self.overlay.is_enabled)
        self.assertFalse(self.overlay._items[0].isVisible())

        self.overlay.set_enabled(True)
        self.assertTrue(self.overlay._items[0].isVisible())


if __name__ == "__main__":
    unittest.main()
