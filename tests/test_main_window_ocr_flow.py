import unittest
from unittest.mock import patch
import numpy as np
import tests.qt_support  # noqa: F401  (çıkışta Qt nesnelerini temizler)
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.ui.components.image_canvas import InteractiveCropRect


class RecordingEngine(IOCREngine):
    """Her çağrıda aldığı görselin boyutunu kaydeder; kırpım uzayında (5,5)-(25,15) kutusu döner."""

    def __init__(self):
        self.shapes = []

    @property
    def name(self) -> str:
        return "Recording"

    @property
    def is_available(self) -> bool:
        return True

    def extract_text(self, image, lang="tur+eng"):
        self.shapes.append(image.shape[:2])
        return OCRResult(
            text="metin",
            confidence=0.9,
            details=[{"text": "metin", "confidence": 0.9, "bbox": [[5, 5], [25, 5], [25, 15], [5, 15]]}],
            success=True,
        )


class TestMainWindowOcrFlow(unittest.TestCase):
    """MainWindow OCR akışı: ROI ofseti, multi_region tam görsel ve tekrar çalıştırma."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from src.ui.main_window import MainWindow
        self.engine = RecordingEngine()
        patcher = patch("src.ui.main_window.OCREngineFactory.get_engine", return_value=self.engine)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.win = MainWindow()
        self.addCleanup(self._dispose_window)
        self.img = np.full((300, 600, 3), 255, dtype=np.uint8)
        self.win.canvas.set_cv_image(self.img)
        self.win.on_image_loaded(self.img)

    def _dispose_window(self):
        worker = self.win._ocr_worker
        if worker is not None:
            worker.wait(5000)
        self.win.close()
        self.win.deleteLater()
        self.app.processEvents()

    def _add_roi(self, x, y, w, h):
        item = InteractiveCropRect(QRectF(x, y, w, h))
        self.win.canvas._crop_items.append(item)
        self.win.canvas.scene().addItem(item)

    def _run_ocr(self):
        self.win.start_ocr_process()
        worker = self.win._ocr_worker
        worker.wait(20000)
        self.app.processEvents()

    def _set_mode(self, mode_id):
        self.win.cmb_scan_mode.setCurrentIndex(self.win.cmb_scan_mode.findData(mode_id))

    def _box_lefts(self):
        return sorted(item.rect().left() for item in self.win.overlay_manager._items)

    def test_single_roi_overlay_is_shifted_into_image_space(self):
        self._set_mode("line")
        self._add_roi(200, 100, 300, 120)
        self._run_ocr()
        self.assertEqual(self.engine.shapes[-1], (120, 300))
        self.assertEqual(self._box_lefts(), [205.0])
        top = self.win.overlay_manager._items[0].rect().top()
        self.assertEqual(top, 105.0)

    def test_multi_region_scans_all_regions_from_full_image(self):
        self._set_mode("multi_region")
        self._add_roi(10, 10, 100, 80)
        self._add_roi(400, 150, 150, 100)
        self._run_ocr()
        self.assertEqual(self.engine.shapes, [(80, 100), (100, 150)])
        text = self.win.text_editor.get_text()
        self.assertIn("[1. Seçili Bölge]", text)
        self.assertIn("[2. Seçili Bölge]", text)
        self.assertEqual(self._box_lefts(), [15.0, 405.0])

    def test_rerun_ocr_and_reload_image_after_overlay_do_not_raise(self):
        self._set_mode("line")
        self._run_ocr()
        self.assertEqual(len(self.win.overlay_manager._items), 1)

        # Filtre değişimi scene'i yeniler; ardından OCR tekrar çalışabilmeli.
        self.win.filter_panel.chk_threshold.setChecked(True)
        self.assertEqual(len(self.win.overlay_manager._items), 0)
        self._run_ocr()
        self.assertEqual(len(self.engine.shapes), 2)
        self.assertEqual(len(self.win.overlay_manager._items), 1)

        # Kutular varken yeni görsel yükleme çökmemeli.
        self.win.on_image_loaded(self.img.copy())
        self.assertEqual(len(self.win.overlay_manager._items), 0)


if __name__ == "__main__":
    unittest.main()
