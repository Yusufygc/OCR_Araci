from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout
)

from src.ui.strings import UIStrings
from src.utils.updater.update_service import UpdateInfo

DIALOG_MIN_WIDTH = 460
NOTES_MIN_HEIGHT = 120


class UpdateDialog(QDialog):
    """
    "Yeni sürüm var" penceresi (yalnızca görünüm): durumu gösterir, kullanıcı eylemlerini sinyal olarak yayar.
    İndirme, kurulum ve yeniden deneme mantığı UpdateController'dadır.
    """
    update_requested = Signal()
    skip_requested = Signal(str)
    wait_cancelled = Signal()
    page_requested = Signal()

    def __init__(self, info: UpdateInfo, current_version: str, parent=None):
        super().__init__(parent)
        self._info = info
        self.setWindowTitle(UIStrings.UPDATE_TITLE)
        self.setMinimumWidth(DIALOG_MIN_WIDTH)
        self._build_ui(current_version)

    def _build_ui(self, current_version: str):
        layout = QVBoxLayout(self)
        self.lbl_title = QLabel(UIStrings.UPDATE_AVAILABLE.format(version=self._info.version, current=current_version))
        layout.addWidget(self.lbl_title)

        self.txt_notes = QPlainTextEdit(self._info.notes or UIStrings.UPDATE_NOTES_EMPTY)
        self.txt_notes.setReadOnly(True)
        self.txt_notes.setMinimumHeight(NOTES_MIN_HEIGHT)
        layout.addWidget(self.txt_notes)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        layout.addLayout(self._build_buttons())

    def _build_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.btn_update = self._button(UIStrings.BTN_UPDATE_NOW, self.update_requested.emit)
        self.btn_skip = self._button(UIStrings.BTN_UPDATE_SKIP, lambda: self.skip_requested.emit(self._info.version))
        self.btn_later = self._button(UIStrings.BTN_UPDATE_LATER, self.reject)
        self.btn_stop_wait = self._button(UIStrings.BTN_UPDATE_STOP_WAIT, self.wait_cancelled.emit)
        self.btn_page = self._button(UIStrings.BTN_UPDATE_PAGE, self.page_requested.emit)
        self.btn_stop_wait.setVisible(False)
        self.btn_page.setVisible(False)
        for button in (self.btn_update, self.btn_skip, self.btn_later, self.btn_stop_wait, self.btn_page):
            row.addWidget(button)
        return row

    @staticmethod
    def _button(text: str, handler) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(handler)
        return button

    def show_downloading(self, done: int = 0, total: int = 0):
        percent = int(done * 100 / total) if total else 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percent)
        self.lbl_status.setText(UIStrings.UPDATE_DOWNLOADING.format(percent=percent))
        for button in (self.btn_update, self.btn_skip, self.btn_later):
            button.setEnabled(False)

    def show_installing(self):
        self.progress_bar.setValue(100)
        self.lbl_status.setText(UIStrings.UPDATE_INSTALLING)
        self.btn_stop_wait.setVisible(False)

    def show_waiting(self, attempt: int, total: int):
        self.lbl_status.setText(UIStrings.UPDATE_WAITING.format(attempt=attempt, total=total))
        self.btn_stop_wait.setVisible(True)

    def show_blocked(self):
        self.lbl_status.setText(UIStrings.UPDATE_BLOCKED)
        self.btn_stop_wait.setVisible(False)
        self.btn_page.setVisible(True)
        self.btn_later.setEnabled(True)

    def show_error(self, message: str):
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(UIStrings.UPDATE_FAILED.format(error=message))
        self.btn_page.setVisible(True)
        for button in (self.btn_update, self.btn_skip, self.btn_later):
            button.setEnabled(True)
