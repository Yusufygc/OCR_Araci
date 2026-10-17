@echo off
echo ============================================
echo   Kusursuz OCR - Kurulum Dosyasi Derleme
echo ============================================
echo.
.\venv\Scripts\python.exe build_installer.py %*
echo.
pause
