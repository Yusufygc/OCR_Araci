# Dağıtım ve Paketleme Mimarisi (PyInstaller & CI)

Bu sayfa, uygulamanın Windows masaüstü için tek klasör/tek dosya `.exe` haline getirilmesini ve GitHub Actions CI süreçlerini açıklar.

İlgili sayfalar: [[architecture]], [[rules]]

---

## 1. PyInstaller Yapılandırması (`ocr_app.spec`)

- **Mod:** `console=False` (GUI pencere modu, arka plan siyah konsol penceresi açılmaz).
- **Veri Paketleme (`datas`):**
  - EasyOCR karakter setleri ve konfigürasyonları `venv/Lib/site-packages/easyocr` dizininden dist klasörüne paketlenir.
- **Dahili Modüller (`hiddenimports`):**
  - `torch`, `torchvision`, `skimage`, `scipy`, `cv2`, `numpy`, `docx`, `lxml`
  - *Gereksinim:* `src.utils.exporters.pdf_exporter` ve PySide6 QtGui modülleri de eklenmelidir.
- **Hariç Tutulanlar (`excludes`):**
  - `matplotlib`, `tkinter`, `IPython`, `jupyter`, `pytest`, `unittest`

---

## 2. Derleme Betiği (`build_exe.bat`)

Tek tıkla derleme için proje kökünde yer alır:
```batch
.\venv\Scripts\pyinstaller.exe --noconfirm ocr_app.spec
```
Çıktı konumu: `dist\KusursuzOCR\KusursuzOCR.exe`.

---

## 3. GitHub Actions CI Boru Hattı (`.github/workflows/test.yml`)

- **Tetikleyiciler:** `main` veya `master` dallarına yapılan her push ve pull request.
- **İşletim Sistemi:** `ubuntu-latest`
- **Adımlar:**
  1. Kod tabanını klonlar (`actions/checkout@v4`).
  2. Python 3.10 kurar (`actions/setup-python@v5`).
  3. Sabitlenmiş bağımlılıkları yükler (`pip install -r requirements.txt`).
  4. Test paketini çalıştırır (`python -m unittest discover tests`).
