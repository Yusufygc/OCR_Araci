DARK_STYLE_SHEET = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    font-size: 13px;
}

QGroupBox {
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #00e676;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 2px 8px;
    background-color: #1e1e1e;
}

QPushButton {
    background-color: #2a2a2a;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 8px 14px;
    color: #ffffff;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #383838;
    border-color: #00e676;
}

QPushButton:pressed {
    background-color: #1f1f1f;
}

QPushButton:disabled {
    background-color: #181818;
    color: #555555;
    border-color: #222222;
}

QPushButton#btn_primary {
    background-color: #00c853;
    color: #000000;
    font-weight: bold;
    font-size: 14px;
    padding: 10px 18px;
}

QPushButton#btn_primary:hover {
    background-color: #00e676;
}

QComboBox {
    background-color: #2a2a2a;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #ffffff;
}

QComboBox::drop-down {
    border: none;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #444444;
    background-color: #2a2a2a;
}

QCheckBox::indicator:checked {
    background-color: #00e676;
    border-color: #00e676;
}

QPlainTextEdit, QTextEdit {
    background-color: #141414;
    border: 1px solid #2d2d2d;
    border-radius: 6px;
    padding: 8px;
    color: #f0f0f0;
    selection-background-color: #00c853;
    selection-color: #000000;
}

QGraphicsView {
    border: 1px solid #2d2d2d;
    background-color: #171717;
    border-radius: 8px;
}

QProgressBar {
    border: 1px solid #333333;
    border-radius: 4px;
    text-align: center;
    background-color: #1a1a1a;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #00e676;
    border-radius: 3px;
}

QStatusBar {
    background-color: #141414;
    color: #999999;
}
"""
