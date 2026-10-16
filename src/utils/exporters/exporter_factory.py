from typing import Dict, Type
from src.utils.exporters.exporter_interface import IDocumentExporter
from src.utils.exporters.txt_exporter import TxtExporter
from src.utils.exporters.docx_exporter import DocxExporter
from src.utils.exporters.pdf_exporter import PdfExporter


class ExporterFactory:
    """Factory Pattern for creating document exporter strategy objects."""

    _exporters: Dict[str, Type[IDocumentExporter]] = {
        "txt": TxtExporter,
        "docx": DocxExporter,
        "pdf": PdfExporter,
    }

    @classmethod
    def get_exporter(cls, format_key: str) -> IDocumentExporter:
        key = format_key.lower().replace(".", "")
        if key not in cls._exporters:
            raise ValueError(f"Unsupported export format: {format_key}")
        return cls._exporters[key]()

    @classmethod
    def get_file_dialog_filters(cls) -> str:
        """Returns combined Qt file dialog filter string."""
        filters = []
        for exporter_cls in cls._exporters.values():
            inst = exporter_cls()
            filters.append(inst.file_filter)
        return ";;".join(filters)
