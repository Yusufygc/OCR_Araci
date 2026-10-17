@echo off
echo ============================================
echo   OCR Aracı - Kurulum Dosyasi Derleme
echo ============================================
echo.
.\venv\Scripts\python.exe build_installer.py %*
echo.
pause
