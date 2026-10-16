from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QCheckBox, 
    QGroupBox, QPushButton
)
from src.ui.strings import UIStrings
from src.ui.icons import IconProvider, IconType


PANEL_SPACING = 8
CHECKBOX_SPACING = 6
GROUP_MARGIN_HORIZ = 12
GROUP_MARGIN_TOP = 16
GROUP_MARGIN_BOTTOM = 12


class FilterPanel(QWidget):
    """
    Control panel for OpenCV image preprocessing options.
    Emits filters_changed signal when any setting is toggled or updated.
    """
    filters_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(PANEL_SPACING)

        group = QGroupBox(UIStrings.GROUP_FILTERS)
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(
            GROUP_MARGIN_HORIZ, GROUP_MARGIN_TOP, GROUP_MARGIN_HORIZ, GROUP_MARGIN_BOTTOM
        )
        group_layout.setSpacing(CHECKBOX_SPACING)

        # Checkboxes
        self.chk_grayscale = QCheckBox(UIStrings.CHK_GRAYSCALE)
        self.chk_contrast = QCheckBox(UIStrings.CHK_CONTRAST)
        self.chk_denoise = QCheckBox(UIStrings.CHK_DENOISE)
        self.chk_threshold = QCheckBox(UIStrings.CHK_THRESHOLD)
        self.chk_remove_color = QCheckBox(UIStrings.CHK_REMOVE_COLOR)
        self.chk_deskew = QCheckBox(UIStrings.CHK_DESKEW)

        # Default settings
        self.chk_contrast.setChecked(True)
        self.chk_denoise.setChecked(True)

        group_layout.addWidget(self.chk_grayscale)
        group_layout.addWidget(self.chk_contrast)
        group_layout.addWidget(self.chk_denoise)
        group_layout.addWidget(self.chk_threshold)
        group_layout.addWidget(self.chk_remove_color)
        group_layout.addWidget(self.chk_deskew)

        # Reset button
        btn_reset = QPushButton(UIStrings.BTN_RESET_FILTERS)
        btn_reset.setIcon(IconProvider.get_icon(IconType.RESET_FILTERS))
        btn_reset.clicked.connect(self.reset_filters)
        group_layout.addWidget(btn_reset)

        layout.addWidget(group)

        # Connect signals
        for chk in [
            self.chk_grayscale, self.chk_contrast, self.chk_denoise, 
            self.chk_threshold, self.chk_remove_color, self.chk_deskew
        ]:
            chk.toggled.connect(lambda: self.filters_changed.emit())

    def get_filter_settings(self) -> dict:
        return {
            "grayscale": self.chk_grayscale.isChecked(),
            "contrast": self.chk_contrast.isChecked(),
            "denoise": self.chk_denoise.isChecked(),
            "threshold": self.chk_threshold.isChecked(),
            "remove_color": self.chk_remove_color.isChecked(),
            "deskew": self.chk_deskew.isChecked()
        }

    def reset_filters(self):
        self.chk_grayscale.setChecked(False)
        self.chk_contrast.setChecked(True)
        self.chk_denoise.setChecked(True)
        self.chk_threshold.setChecked(False)
        self.chk_remove_color.setChecked(False)
        self.chk_deskew.setChecked(False)
        self.filters_changed.emit()
