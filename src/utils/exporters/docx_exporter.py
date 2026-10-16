from src.utils.exporters.exporter_interface import IDocumentExporter


class DocxExporter(IDocumentExporter):
    """Exports text to Word .docx format."""

    @property
    def file_extension(self) -> str:
        return ".docx"

    @property
    def file_filter(self) -> str:
        return "Word Belgesi (*.docx)"

    def export(self, text: str, output_path: str) -> bool:
        try:
            import docx
            doc = docx.Document()
            for line in text.split("\n"):
                doc.add_paragraph(line)
            doc.save(output_path)
            return True
        except Exception:
            return False
