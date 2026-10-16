from src.utils.exporters.exporter_interface import IDocumentExporter


class TxtExporter(IDocumentExporter):
    """Exports text to plain .txt format."""

    @property
    def file_extension(self) -> str:
        return ".txt"

    @property
    def file_filter(self) -> str:
        return "Metin Dosyası (*.txt)"

    def export(self, text: str, output_path: str) -> bool:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return True
