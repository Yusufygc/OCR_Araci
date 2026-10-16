@echo off
echo ============================================
echo   Kusursuz OCR - EXE Build Script
echo ============================================
echo.

REM Activate venv and run PyInstaller with the spec file
echo [1/2] PyInstaller ile derleme baslatiliyor...
.\venv\Scripts\pyinstaller.exe --noconfirm ocr_app.spec

echo.
if exist "dist\KusursuzOCR\KusursuzOCR.exe" (
    echo [2/2] BASARILI! EXE dosyasi olusturuldu:
    echo        dist\KusursuzOCR\KusursuzOCR.exe
) else (
    echo [HATA] EXE dosyasi olusturulamadi. Loglari kontrol edin.
)

echo.
pause
