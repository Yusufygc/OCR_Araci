"""
Merkezi İkon Sağlayıcı Mekanizması (Icon Provider).
Platform-native Qt standart ikonlarını ve gerektiğinde özel görsel ikonları tek merkezden sunar.
"""

from enum import Enum, auto
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle


class IconType(Enum):
    OPEN_IMAGE = auto()
    RUN_OCR = auto()
    RESET_FILTERS = auto()
    COPY_TEXT = auto()
    EXPORT_TXT = auto()
    EXPORT_DOCX = auto()
    EXPORT_PDF = auto()


class IconProvider:
    """
    Merkezi İkon Sağlayıcı Sınıfı.
    Emoji yerine temiz, tutarlı ve işletim sistemi standartlarına uygun QIcon nesneleri sağlar.
    """

    _STANDARD_PIXMAP_MAP = {
        IconType.OPEN_IMAGE: QStyle.StandardPixmap.SP_DialogOpenButton,
        IconType.RUN_OCR: QStyle.StandardPixmap.SP_MediaPlay,
        IconType.RESET_FILTERS: QStyle.StandardPixmap.SP_BrowserReload,
        IconType.COPY_TEXT: QStyle.StandardPixmap.SP_FileDialogDetailedView,
        IconType.EXPORT_TXT: QStyle.StandardPixmap.SP_DialogSaveButton,
        IconType.EXPORT_DOCX: QStyle.StandardPixmap.SP_DialogSaveButton,
        IconType.EXPORT_PDF: QStyle.StandardPixmap.SP_DialogSaveButton,
    }

    @classmethod
    def get_icon(cls, icon_type: IconType) -> QIcon:
        """Belirtilen ikon tipi için platform-native QIcon döner."""
        pixmap_enum = cls._STANDARD_PIXMAP_MAP.get(icon_type)
        if pixmap_enum is None:
            return QIcon()

        app = QApplication.instance()
        if app is not None and app.style() is not None:
            return app.style().standardIcon(pixmap_enum)

        return QIcon()
