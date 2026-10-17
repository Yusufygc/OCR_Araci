import os
from typing import Optional
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QComboBox, QCheckBox, QLabel, QFileDialog, 
    QProgressBar, QMessageBox, QApplication
)

from src.ui.components.image_canvas import ImageCanvas
from src.ui.components.filter_panel import FilterPanel
from src.ui.components.text_editor import TextEditorPanel
from src.ui.components.overlay_manager import CanvasOverlayManager
from src.ui.update_controller import UpdateController
from src.ui.workers.ocr_worker import OCRWorkerThread
from src.core.processing.image_processor import ImageProcessor
from src.core.factories.ocr_factory import OCREngineFactory
from src.core.strategies.scan_factory import ScanStrategyFactory
from src.core.interfaces.ocr_interface import OCRResult
from src.ui.strings import UIStrings
from src.ui.icons import IconProvider, IconType

DEFAULT_WINDOW_WIDTH = 1295
DEFAULT_WINDOW_HEIGHT = 800
ENGINE_COMBO_MIN_WIDTH = 135
SCAN_MODE_COMBO_MIN_WIDTH = 135
LANG_COMBO_MIN_WIDTH = 95
TOP_BAR_SPACING = 6
SECTION_SPACING = 8
WINDOW_MARGIN = 10
THREAD_WAIT_TIMEOUT_MS = 1500
STATUS_SNIPPET_MAX_LEN = 30
STATUS_MSG_TIMEOUT_MS = 3000



class MainWindow(QMainWindow):
    """
    Main Window Application Controller (PySide6).
    Coordinates Image Canvas, Preprocessing Pipeline, OCR Strategy Execution,
    and Output Exporting cleanly using Qt Signals and Loose Coupling.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle(UIStrings.APP_TITLE)
        self._is_centered = False
        self._raw_image: Optional[np.ndarray] = None
        self._processed_image: Optional[np.ndarray] = None
        self._ocr_worker: Optional[OCRWorkerThread] = None
        self._ocr_offset = (0, 0)

        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.init_ui()
        self.center_on_screen()

    def center_on_screen(self):
        """Centers the window on the active primary screen."""
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            return
        screen_geom = screen.availableGeometry()
        if screen_geom.isEmpty():
            return

        x = screen_geom.left() + max(0, (screen_geom.width() - DEFAULT_WINDOW_WIDTH) // 2)
        y = screen_geom.top() + max(0, (screen_geom.height() - DEFAULT_WINDOW_HEIGHT) // 2)
        self.move(x, y)

    def showEvent(self, event):
        """Ensures the window is properly positioned and centered upon first display."""
        super().showEvent(event)
        if not self._is_centered:
            self.center_on_screen()
            self._is_centered = True

    def _build_top_bar(self) -> QHBoxLayout:
        top_bar = QHBoxLayout()
        top_bar.setSpacing(TOP_BAR_SPACING)

        btn_open = QPushButton(UIStrings.BTN_OPEN_IMAGE)
        btn_open.setIcon(IconProvider.get_icon(IconType.OPEN_IMAGE))
        btn_open.clicked.connect(self.open_image_dialog)
        top_bar.addWidget(btn_open)

        lbl_engine = QLabel(UIStrings.LBL_ENGINE)
        top_bar.addWidget(lbl_engine)

        self.cmb_engine = QComboBox()
        self.cmb_engine.setMinimumWidth(ENGINE_COMBO_MIN_WIDTH)
        self.cmb_engine.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._populate_engine_combo()
        top_bar.addWidget(self.cmb_engine)

        lbl_scan_mode = QLabel(UIStrings.LBL_SCAN_MODE)
        top_bar.addWidget(lbl_scan_mode)

        self.cmb_scan_mode = QComboBox()
        self.cmb_scan_mode.setMinimumWidth(SCAN_MODE_COMBO_MIN_WIDTH)
        self.cmb_scan_mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self._populate_scan_modes()
        top_bar.addWidget(self.cmb_scan_mode)

        lbl_lang = QLabel(UIStrings.LBL_LANGUAGE)
        top_bar.addWidget(lbl_lang)

        self.cmb_lang = QComboBox()
        self.cmb_lang.setMinimumWidth(LANG_COMBO_MIN_WIDTH)
        self.cmb_lang.addItem(UIStrings.LANG_TUR_ENG, "tur+eng")
        self.cmb_lang.addItem(UIStrings.LANG_TUR, "tur")
        self.cmb_lang.addItem(UIStrings.LANG_ENG, "eng")
        top_bar.addWidget(self.cmb_lang)

        top_bar.addStretch()
        return top_bar

    def _build_bottom_box(self) -> QHBoxLayout:
        bottom_box = QHBoxLayout()
        self.filter_panel = FilterPanel()
        self.filter_panel.filters_changed.connect(self.apply_image_filters)
        bottom_box.addWidget(self.filter_panel, stretch=1)

        ocr_action_box = QVBoxLayout()
        self.btn_run_ocr = QPushButton(UIStrings.BTN_RUN_OCR)
        self.btn_run_ocr.setIcon(IconProvider.get_icon(IconType.RUN_OCR))
        self.btn_run_ocr.setObjectName("btn_primary")
        self.btn_run_ocr.clicked.connect(self.start_ocr_process)
        ocr_action_box.addWidget(self.btn_run_ocr)

        self.chk_overlay = QCheckBox(UIStrings.CHK_SHOW_OVERLAY)
        self.chk_overlay.setChecked(True)
        self.chk_overlay.toggled.connect(self.on_overlay_toggled)
        ocr_action_box.addWidget(self.chk_overlay)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        ocr_action_box.addWidget(self.progress_bar)

        self.lbl_status = QLabel(UIStrings.STATUS_READY)
        self.lbl_status.setWordWrap(True)
        ocr_action_box.addWidget(self.lbl_status)

        bottom_box.addLayout(ocr_action_box, stretch=1)
        return bottom_box

    def _build_left_panel(self) -> QWidget:
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addLayout(self._build_top_bar())

        self.canvas = ImageCanvas()
        self.canvas.image_loaded.connect(self.on_image_loaded)
        left_layout.addWidget(self.canvas, stretch=2)

        left_layout.addLayout(self._build_bottom_box())
        return left_widget

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN, WINDOW_MARGIN)
        main_layout.setSpacing(SECTION_SPACING)

        # Sol taraf: Resim onizleme ve araclar (Simetrik %50)
        left_panel = self._build_left_panel()
        main_layout.addWidget(left_panel, stretch=1)

        # Sag taraf: Cikti metin editoru (Simetrik %50)
        self.text_editor = TextEditorPanel()
        main_layout.addWidget(self.text_editor, stretch=1)

        self.overlay_manager = CanvasOverlayManager(self.canvas)
        self.overlay_manager.box_clicked.connect(self.on_box_clicked)

        self.statusBar().showMessage(UIStrings.STATUS_BAR_READY)

        self.update_controller = UpdateController(self)
        self.update_controller.install_menu(self.menuBar())
        self.update_controller.quit_requested.connect(self.close)

    def _populate_engine_combo(self):
        self.cmb_engine.clear()
        engines = OCREngineFactory.list_available_engines()
        for eng in engines:
            name = eng["name"]
            if not eng["available"]:
                name += " (Kütüphane eksik)"
            self.cmb_engine.addItem(name, eng["id"])

    def _populate_scan_modes(self):
        self.cmb_scan_mode.clear()
        for mode in ScanStrategyFactory.list_strategies():
            self.cmb_scan_mode.addItem(mode["name"], mode["id"])
        idx = self.cmb_scan_mode.findData("block")
        if idx >= 0:
            self.cmb_scan_mode.setCurrentIndex(idx)

    def on_overlay_toggled(self, checked: bool):
        self.overlay_manager.set_enabled(checked)

    def on_box_clicked(self, text: str):
        suffix = "..." if len(text) > STATUS_SNIPPET_MAX_LEN else ""
        snippet = text[:STATUS_SNIPPET_MAX_LEN] + suffix
        self.statusBar().showMessage(UIStrings.STATUS_BOX_COPIED.format(text=snippet), STATUS_MSG_TIMEOUT_MS)

    def open_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, UIStrings.DIALOG_OPEN_IMAGE, "", UIStrings.FILTER_IMAGE_FILES
        )
        if file_path:
            try:
                img = ImageProcessor.load_image(file_path)
                self._raw_image = img
                self.canvas.set_cv_image(img)
                self.overlay_manager.clear()
                self.apply_image_filters()
                self.lbl_status.setText(UIStrings.STATUS_LOADED.format(filename=os.path.basename(file_path)))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Görsel okunamadı: {str(e)}")

    def on_image_loaded(self, cv_img: np.ndarray):
        self._raw_image = cv_img
        self.overlay_manager.clear()
        self.apply_image_filters()
        self.lbl_status.setText(UIStrings.STATUS_DRAG_DROPPED)

    def apply_image_filters(self):
        """Applies enabled OpenCV preprocessing filters cleanly."""
        if self._raw_image is None:
            return

        settings = self.filter_panel.get_filter_settings()
        img = self._raw_image.copy()

        if settings["remove_color"]:
            img = ImageProcessor.remove_color_annotations(img)
        if settings["deskew"]:
            img = ImageProcessor.deskew(img)
        if settings["denoise"]:
            img = ImageProcessor.denoise(img)
        if settings["contrast"]:
            img = ImageProcessor.enhance_contrast(img)
        if settings["grayscale"]:
            img = ImageProcessor.to_grayscale(img)
        if settings["threshold"]:
            img = ImageProcessor.binarize_adaptive(img)

        self._processed_image = img
        self.canvas.set_cv_image(img, reset_crop=False)
        if hasattr(self, "overlay_manager"):
            self.overlay_manager.clear()

    def _resolve_ocr_engine(self, engine_key: str):
        try:
            ocr_engine = OCREngineFactory.get_engine(engine_key)
            if not ocr_engine.is_available:
                QMessageBox.critical(self, "Hata", UIStrings.MSG_ENGINE_NOT_AVAILABLE.format(engine_name=ocr_engine.name))
                return None
            return ocr_engine
        except Exception as e:
            QMessageBox.critical(self, "Hata", UIStrings.MSG_ENGINE_CREATE_ERROR.format(error=str(e)))
            return None

    def _resolve_scan_strategy(self, mode_id: str):
        strategy = ScanStrategyFactory.get_strategy(mode_id)
        if mode_id == "multi_region" and hasattr(strategy, "set_regions"):
            strategy.set_regions(self.canvas.get_selected_regions())
        return strategy

    def start_ocr_process(self):
        """Launches non-blocking OCR worker thread."""
        scan_mode = self.cmb_scan_mode.currentData()
        if scan_mode == "multi_region":
            # Strateji kendi bölgelerini tam görselden (görsel koordinatlarıyla) keser.
            target_image = self.canvas.get_full_cv_image()
            self._ocr_offset = (0, 0)
        else:
            target_image = self.canvas.get_cropped_cv_image()
            self._ocr_offset = self.canvas.get_primary_region_offset()
        if target_image is None:
            QMessageBox.warning(self, "Uyarı", UIStrings.MSG_NO_IMAGE_BODY)
            return

        ocr_engine = self._resolve_ocr_engine(self.cmb_engine.currentData())
        if ocr_engine is None:
            return

        strategy = self._resolve_scan_strategy(scan_mode)
        self.overlay_manager.clear()
        self.btn_run_ocr.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText(UIStrings.STATUS_PROCESSING)

        self._ocr_worker = OCRWorkerThread(
            ocr_engine, target_image, lang=self.cmb_lang.currentData(), strategy=strategy
        )
        self._ocr_worker.result_ready.connect(self.on_ocr_success)
        self._ocr_worker.error_occurred.connect(self.on_ocr_error)
        self._ocr_worker.start()

    def on_ocr_success(self, result: OCRResult):
        self.btn_run_ocr.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result.success:
            self.text_editor.set_text(result.text)
            offset_x, offset_y = self._ocr_offset
            self.overlay_manager.render_boxes(
                ImageProcessor.shift_details_coordinates(result.details, offset_x, offset_y)
            )
            self.lbl_status.setText(UIStrings.STATUS_SUCCESS.format(time=result.processing_time, confidence=result.confidence*100))
            self.statusBar().showMessage(UIStrings.STATUS_BAR_SUCCESS.format(time=result.processing_time))
        else:
            QMessageBox.critical(self, "OCR Hatası", result.error_message)
            self.lbl_status.setText(UIStrings.STATUS_ERROR)

    def on_ocr_error(self, err_msg: str):
        self.btn_run_ocr.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Hata", UIStrings.MSG_UNEXPECTED_ERROR.format(error=err_msg))
        self.lbl_status.setText(UIStrings.STATUS_FAILED)

    def closeEvent(self, event):
        """Ensures background worker threads terminate cleanly on window close."""
        if self._ocr_worker and self._ocr_worker.isRunning():
            self._ocr_worker.requestInterruption()
            self._ocr_worker.quit()
            self._ocr_worker.wait(THREAD_WAIT_TIMEOUT_MS)
        event.accept()

