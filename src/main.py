import os
import sys
import logging
import warnings

# Configure unified application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Suppress internal PyTorch deprecation & hardware user warnings for clean console output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)


def _resolve_base_path() -> str:
    """
    Resolves the application base path for both:
    - Development mode (python src/main.py from any working directory)
    - Frozen mode (PyInstaller .exe bundle, single-file or single-folder)
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running as Python script — project root is one level above src/
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


BASE_PATH = _resolve_base_path()

# Ensure project root is discoverable for all internal `from src.xxx` imports
if BASE_PATH not in sys.path:
    sys.path.insert(0, BASE_PATH)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.styles import DARK_STYLE_SHEET
from src.ui.icons import IconProvider
from src.version import EXE_NAME


def _set_taskbar_identity():
    """Windows görev çubuğunda Python yerine uygulamanın kendi ikonunun görünmesi için süreç kimliği."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{EXE_NAME}.App")


def main():
    # Enable High DPI Scaling for crisp fonts and graphics on modern screens
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE_SHEET)
    _set_taskbar_identity()
    app.setWindowIcon(IconProvider.get_app_icon())

    window = MainWindow()
    window.show()
    window.update_controller.schedule_startup_check()  # init içinde değil: testler ağa çıkmasın

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
