from src.utils.exporters.exporter_interface import IDocumentExporter


class PdfExporter(IDocumentExporter):
    """Exports text to PDF format using PySide6 QPdfWriter."""

    @property
    def file_extension(self) -> str:
        return ".pdf"

    @property
    def file_filter(self) -> str:
        return "PDF Belgesi (*.pdf)"

    def export(self, text: str, output_path: str) -> bool:
        try:
            import sys
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QPdfWriter, QTextDocument, QPageSize

            # Ensure QApplication exists for GUI/rendering classes
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            writer = QPdfWriter(output_path)
            writer.setPageSize(QPageSize.A4)

            doc = QTextDocument()
            doc.setPlainText(text)
            doc.print_(writer)
            return True
        except Exception:
            return False
