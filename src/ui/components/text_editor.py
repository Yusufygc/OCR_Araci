from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, 
    QPushButton, QLabel, QFileDialog, QMessageBox, QGroupBox
)
from PySide6.QtGui import QFont, QGuiApplication
from src.utils.exporters.exporter_factory import ExporterFactory
from src.ui.strings import UIStrings
from src.ui.icons import IconProvider, IconType


class TextEditorPanel(QWidget):
    """
    Rich Text Output Panel.
    Provides live statistics, copy to clipboard, and multi-format document exporting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        group = QGroupBox(UIStrings.GROUP_OUTPUT)
        group_layout = QVBoxLayout(group)

        # Plain Text Editor
        self.editor = QPlainTextEdit()
        font = QFont("Consolas", 11)
        self.editor.setFont(font)
        self.editor.setPlaceholderText(UIStrings.EDITOR_PLACEHOLDER)
        self.editor.textChanged.connect(self._update_stats)

        group_layout.addWidget(self.editor)

        # Stats Bar
        self.lbl_stats = QLabel(UIStrings.STATS_FORMAT.format(words=0, chars=0, lines=0))
        self.lbl_stats.setStyleSheet("color: #888888; font-size: 11px;")
        group_layout.addWidget(self.lbl_stats)

        # Action Buttons Layout
        btn_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton(UIStrings.BTN_COPY_TEXT)
        self.btn_copy.setIcon(IconProvider.get_icon(IconType.COPY_TEXT))
        self.btn_copy.setStyleSheet("background-color: #2b5278; font-weight: bold; padding: 6px;")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)

        self.btn_export_txt = QPushButton(UIStrings.BTN_EXPORT_TXT)
        self.btn_export_txt.setIcon(IconProvider.get_icon(IconType.EXPORT_TXT))
        self.btn_export_txt.clicked.connect(lambda: self.export_document("txt"))

        self.btn_export_docx = QPushButton(UIStrings.BTN_EXPORT_DOCX)
        self.btn_export_docx.setIcon(IconProvider.get_icon(IconType.EXPORT_DOCX))
        self.btn_export_docx.clicked.connect(lambda: self.export_document("docx"))

        self.btn_export_pdf = QPushButton(UIStrings.BTN_EXPORT_PDF)
        self.btn_export_pdf.setIcon(IconProvider.get_icon(IconType.EXPORT_PDF))
        self.btn_export_pdf.clicked.connect(lambda: self.export_document("pdf"))

        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_export_txt)
        btn_layout.addWidget(self.btn_export_docx)
        btn_layout.addWidget(self.btn_export_pdf)

        group_layout.addLayout(btn_layout)
        layout.addWidget(group)

    def set_text(self, text: str):
        self.editor.setPlainText(text)
        self._update_stats()

    def get_text(self) -> str:
        return self.editor.toPlainText()

    def _update_stats(self):
        text = self.editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        line_count = len(text.splitlines()) if text.strip() else 0
        self.lbl_stats.setText(UIStrings.STATS_FORMAT.format(words=word_count, chars=char_count, lines=line_count))

    def copy_to_clipboard(self):
        text = self.get_text()
        if not text.strip():
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, UIStrings.MSG_COPIED_TITLE, UIStrings.MSG_COPIED_BODY)

    def export_document(self, format_key: str):
        text = self.get_text()
        if not text.strip():
            QMessageBox.warning(self, UIStrings.MSG_NO_TEXT_TITLE, UIStrings.MSG_NO_TEXT_BODY)
            return

        try:
            exporter = ExporterFactory.get_exporter(format_key)
            dialog_title = UIStrings.DIALOG_SAVE_TITLE.format(format_name=format_key.upper())
            file_path, _ = QFileDialog.getSaveFileName(
                self, dialog_title, "", exporter.file_filter
            )
            if file_path:
                if not file_path.endswith(exporter.file_extension):
                    file_path += exporter.file_extension
                
                success = exporter.export(text, file_path)
                if success:
                    QMessageBox.information(self, "Başarılı", UIStrings.MSG_SAVE_SUCCESS.format(path=file_path))
                else:
                    QMessageBox.critical(self, "Hata", UIStrings.MSG_SAVE_ERROR)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma hatası: {str(e)}")
