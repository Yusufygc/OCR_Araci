# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File — Kusursuz OCR Desktop App
Generates a single-folder distribution with all EasyOCR data and PySide6 binaries bundled.

Usage:
    .\venv\Scripts\pyinstaller.exe --noconfirm ocr_app.spec
"""

import os
import sys

block_cipher = None

# Locate venv site-packages reliably
venv_sp = os.path.join(os.path.dirname(sys.executable), '..', 'Lib', 'site-packages')
venv_sp = os.path.abspath(venv_sp)

easyocr_path = os.path.join(venv_sp, 'easyocr')

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Bundle EasyOCR character sets, configs, and model definitions
        (easyocr_path, 'easyocr'),
    ],
    hiddenimports=[
        'easyocr',
        'easyocr.easyocr',
        'easyocr.detection',
        'easyocr.recognition',
        'easyocr.utils',
        'easyocr.imgproc',
        'easyocr.craft_utils',
        'easyocr.config',
        'torch',
        'torchvision',
        'skimage',
        'skimage.io',
        'scipy',
        'PIL',
        'cv2',
        'numpy',
        'docx',
        'lxml',
        'lxml._elementpath',
        'lxml.etree',
        'src.utils.exporters.pdf_exporter',
        'src.utils.exporters.docx_exporter',
        'src.utils.exporters.txt_exporter',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'unittest',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KusursuzOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed mode (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)
