import os
import unittest
from src.utils.exporters.exporter_factory import ExporterFactory
from src.utils.exporters.txt_exporter import TxtExporter
from src.utils.exporters.docx_exporter import DocxExporter
from src.utils.exporters.pdf_exporter import PdfExporter


class TestExporters(unittest.TestCase):
    """Unit tests for document export strategies and factory."""

    def setUp(self):
        self.sample_text = "Örnek OCR Metni:\n1. Satır: Türkçe karakterler ç, ş, ğ, ö, ü, ı, İ.\n2. Satır: 1234567890."
        self.test_files = []

    def tearDown(self):
        for path in self.test_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_factory_supported_formats(self):
        for fmt in ["txt", ".txt", "TXT", "docx", ".DOCX", "pdf", ".pdf", "PDF"]:
            exporter = ExporterFactory.get_exporter(fmt)
            self.assertIsNotNone(exporter)

    def test_factory_unsupported_format(self):
        with self.assertRaises(ValueError):
            ExporterFactory.get_exporter("xlsx")
        with self.assertRaises(ValueError):
            ExporterFactory.get_exporter("unknown")

    def test_factory_dialog_filters(self):
        filters = ExporterFactory.get_file_dialog_filters()
        self.assertIn("*.txt", filters)
        self.assertIn("*.docx", filters)
        self.assertIn("*.pdf", filters)

    def test_txt_exporter(self):
        exporter = TxtExporter()
        self.assertEqual(exporter.file_extension, ".txt")
        self.assertIn(".txt", exporter.file_filter)

        target_file = "test_export_output.txt"
        self.test_files.append(target_file)

        success = exporter.export(self.sample_text, target_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(target_file))

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, self.sample_text)

    def test_docx_exporter(self):
        exporter = DocxExporter()
        self.assertEqual(exporter.file_extension, ".docx")
        self.assertIn(".docx", exporter.file_filter)

        target_file = "test_export_output.docx"
        self.test_files.append(target_file)

        success = exporter.export(self.sample_text, target_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(target_file))
        self.assertGreater(os.path.getsize(target_file), 0)

    def test_pdf_exporter(self):
        exporter = PdfExporter()
        self.assertEqual(exporter.file_extension, ".pdf")
        self.assertIn(".pdf", exporter.file_filter)

        target_file = "test_export_output.pdf"
        self.test_files.append(target_file)

        success = exporter.export(self.sample_text, target_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(target_file))
        self.assertGreater(os.path.getsize(target_file), 0)


if __name__ == "__main__":
    unittest.main()
