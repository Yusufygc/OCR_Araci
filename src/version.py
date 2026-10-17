"""Tek sürüm kaynağı. `tools/release.py` bu dosyayı günceller; elle düzenleme."""

__version__ = "1.0.0"

# Güncelleme denetiminin bakacağı GitHub deposu ("sahip/depo"). Boşsa güncelleme denetimi kapalıdır.
RELEASE_REPO = "Yusufygc/OCR_Araci"

APP_NAME = "OCR Aracı"
EXE_NAME = "OCRAraci"
INSTALLER_PREFIX = "OCRAraci"
UPDATE_ENV_DISABLE = "OCRARACI_NO_UPDATE_CHECK"
SELFTEST_OUT_ENV = "OCRARACI_SELFTEST_OUT"
