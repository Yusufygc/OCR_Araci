from abc import ABC, abstractmethod


class IDocumentExporter(ABC):
    """Abstract Base Class for Document Exporters (Strategy Pattern)."""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Returns file extension string, e.g. '.txt'."""
        pass

    @property
    @abstractmethod
    def file_filter(self) -> str:
        """Returns Qt File Dialog filter string, e.g. 'Text Files (*.txt)'."""
        pass

    @abstractmethod
    def export(self, text: str, output_path: str) -> bool:
        """Exports text to target path."""
        pass
