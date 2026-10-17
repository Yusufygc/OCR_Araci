import sys
import unittest
import numpy as np
import tests.qt_support  # noqa: F401  (çıkışta Qt nesnelerini temizler)
from PySide6.QtWidgets import QApplication
from src.ui.components.text_editor import TextEditorPanel
from src.ui.components.filter_panel import FilterPanel
from src.ui.components.image_canvas import ImageCanvas


app = QApplication.instance() or QApplication(sys.argv)


class TestUIComponents(unittest.TestCase):
    """Unit tests for UI component behavior, state management and statistics."""

    def test_text_editor_stats(self):
        panel = TextEditorPanel()
        self.assertEqual(panel.get_text(), "")
        self.assertIn("Kelime: 0", panel.lbl_stats.text())

        panel.set_text("Bir iki üç\nDört beş")
        self.assertEqual(panel.get_text(), "Bir iki üç\nDört beş")
        self.assertIn("Kelime: 5", panel.lbl_stats.text())
        self.assertIn("Satır: 2", panel.lbl_stats.text())

    def test_text_editor_strip_region_headers(self):
        panel = TextEditorPanel()
        raw_text = "[1. Bölge]\nFinansal\nVeriler\n\n[2. Bölge]\nHaberler &\nSosyal Medya"
        clean = panel.strip_region_headers(raw_text)
        self.assertNotIn("[1. Bölge]", clean)
        self.assertNotIn("[2. Bölge]", clean)
        self.assertIn("Finansal\nVeriler", clean)
        self.assertIn("Haberler &\nSosyal Medya", clean)

    def test_filter_panel_initial_state(self):
        panel = FilterPanel()
        self.assertTrue(panel.chk_contrast.isChecked())
        self.assertTrue(panel.chk_denoise.isChecked())
        self.assertFalse(panel.chk_grayscale.isChecked())

        # Reset filters test
        panel.chk_grayscale.setChecked(True)
        panel.reset_filters()
        self.assertTrue(panel.chk_contrast.isChecked())
        self.assertFalse(panel.chk_grayscale.isChecked())

    def test_image_canvas_set_image(self):
        canvas = ImageCanvas()
        dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)
        canvas.set_cv_image(dummy_img)
        self.assertIsNotNone(canvas._current_cv_image)
        self.assertEqual(canvas._current_cv_image.shape, (100, 200, 3))

    def test_image_canvas_crop_methods(self):
        canvas = ImageCanvas()
        dummy_img = np.zeros((120, 160, 3), dtype=np.uint8)
        canvas.set_cv_image(dummy_img)

        # Full image returned when no crop exists
        cropped = canvas.get_cropped_cv_image()
        self.assertIsNotNone(cropped)
        self.assertEqual(cropped.shape, dummy_img.shape)

        canvas.clear_crop()
        self.assertIsNone(canvas._crop_item)

    def test_main_window_creation(self):
        from PySide6.QtWidgets import QHBoxLayout
        from src.ui.main_window import MainWindow, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, ENGINE_COMBO_MIN_WIDTH
        win = MainWindow()
        self.assertIsNotNone(win.canvas)
        self.assertIsNotNone(win.filter_panel)
        self.assertIsNotNone(win.text_editor)
        self.assertIsNotNone(win.cmb_engine)
        self.assertIsNotNone(win.cmb_lang)
        self.assertEqual(win.minimumWidth(), DEFAULT_WINDOW_WIDTH)
        self.assertEqual(win.minimumHeight(), DEFAULT_WINDOW_HEIGHT)
        self.assertEqual(win.width(), 1295)
        self.assertEqual(win.height(), 800)
        self.assertGreaterEqual(win.cmb_engine.minimumWidth(), ENGINE_COMBO_MIN_WIDTH)

        # Symmetrical 1:1 layout without QSplitter
        layout = win.centralWidget().layout()
        self.assertIsInstance(layout, QHBoxLayout)
        self.assertEqual(layout.count(), 2)
        self.assertEqual(layout.stretch(0), 1)
        self.assertEqual(layout.stretch(1), 1)

    def test_main_window_centering(self):
        from src.ui.main_window import MainWindow
        win = MainWindow()
        win.center_on_screen()
        self.assertEqual(win.width(), 1295)
        self.assertEqual(win.height(), 800)


if __name__ == "__main__":
    unittest.main()
