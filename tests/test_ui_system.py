import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import sys

from src.ui.strings import UIStrings
from src.ui.icons import IconProvider, IconType

app = QApplication.instance() or QApplication(sys.argv)


class TestUISystem(unittest.TestCase):
    """Unit tests for centralized strings and icon provider mechanism."""

    def test_ui_strings_constants(self):
        self.assertIsInstance(UIStrings.APP_TITLE, str)
        self.assertGreater(len(UIStrings.APP_TITLE), 0)
        self.assertIsInstance(UIStrings.BTN_RUN_OCR, str)
        self.assertIsInstance(UIStrings.BTN_OPEN_IMAGE, str)
        self.assertIsInstance(UIStrings.GROUP_FILTERS, str)
        self.assertIsInstance(UIStrings.GROUP_OUTPUT, str)

        # Ensure no emojis in key strings
        for text in [
            UIStrings.BTN_OPEN_IMAGE,
            UIStrings.BTN_RUN_OCR,
            UIStrings.GROUP_FILTERS,
            UIStrings.GROUP_OUTPUT,
            UIStrings.BTN_RESET_FILTERS,
            UIStrings.BTN_COPY_TEXT,
            UIStrings.BTN_EXPORT_TXT,
            UIStrings.BTN_EXPORT_DOCX,
            UIStrings.BTN_EXPORT_PDF
        ]:
            # Simple heuristic check: ASCII or common Turkish letters, no high Unicode surrogate emojis
            self.assertTrue(all(ord(ch) < 0x2000 for ch in text), f"Emoji found in text: {text}")

    def test_app_icon_is_valid_and_multi_size(self):
        icon = IconProvider.get_app_icon()
        self.assertFalse(icon.isNull())
        self.assertGreaterEqual(max(size.width() for size in icon.availableSizes()), 256)

    def test_main_window_uses_application_icon(self):
        app.setWindowIcon(IconProvider.get_app_icon())
        from src.ui.main_window import MainWindow
        window = MainWindow()
        self.assertFalse(window.windowIcon().isNull())

    def test_icon_provider(self):
        for icon_type in IconType:
            icon = IconProvider.get_icon(icon_type)
            self.assertIsInstance(icon, QIcon)
            self.assertFalse(icon.isNull(), f"Icon should be valid for {icon_type}")


if __name__ == "__main__":
    unittest.main()
