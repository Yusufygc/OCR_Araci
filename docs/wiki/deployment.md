# Dağıtım ve Paketleme Mimarisi (PyInstaller, Inno Setup & CI)

Bu sayfa, uygulamanın Windows masaüstü için paketlenmesinin ve CI süreçlerinin özetidir. Ayrıntılar ayrı sayfalardadır:

- [[exe_distribution]] — kararlı exe tasarımı, Akıllı Uygulama Denetimi (SAC) gerekçesi, Inno betiği, derleme/doğrulama betikleri.
- [[release_process]] — sürüm numarası, etiketle yayın, kontrol listesi, geri alma.
- [[update_system]] — uygulama içi güncelleme.

İlgili sayfalar: [[architecture]], [[rules]]

---

## 1. Paketleme Özeti

- **Araç zinciri:** PyInstaller `6.22.3` (`requirements-build.txt`, sabit) `--onedir --windowed --noupx --debug=noarchive` + Inno Setup 6. Eski `ocr_app.spec` kaldırıldı; bağımsız değişkenler `build_exe.py` içindedir.
- **Kararlı exe:** `packaging/launcher.py` (3 satır, `src.main.main()` çağırır) her sürümde bayt bayt aynı `KusursuzOCR.exe`'yi üretir; onaylı özet `packaging/launcher.sha256` dosyasındadır. Sürümle değişen kod `_internal` altında `.pyc` olarak durur ([[exe_distribution]]).
- **Veri/bağımlılıklar:** `--collect-data=easyocr`, `--collect-submodules=easyocr`, `--collect-submodules=src` ve `torch`, `torchvision`, `skimage`, `scipy`, `cv2`, `numpy`, `docx`, `lxml` için `--hidden-import`. Hariç tutulanlar: `matplotlib`, `tkinter`, `IPython`, `jupyter`, `notebook`, `pytest` (`unittest` torch için bilerek hariç tutulmaz).
- **Tesseract paketlenmez**; ayrıca kurulmalıdır. EasyOCR modelleri ilk kullanımda indirilir.

## 2. Derleme

```powershell
pip install -r requirements.txt -r requirements-build.txt
python build_installer.py            # kararlı exe + kurulum dosyası + .sha256 (dist\installer\)
```

`build_exe.bat` aynı komutu çalıştırır. Seçenekler ve akış: [[exe_distribution]] bölüm 4. Sürüm tek kaynağı `src/version.py`'dir ([[release_process]]).

## 3. GitHub Actions

| İş akışı | Tetikleyici | Ortam | Görev |
|---|---|---|---|
| `.github/workflows/test.yml` | `main`/`master` push ve PR | `ubuntu-latest` | Python 3.10, `pip install -r requirements.txt`, `QT_QPA_PLATFORM=offscreen python -m unittest discover tests` |
| `.github/workflows/release.yml` | `v*` etiketi push | `windows-latest` | Etiket denetimi -> testler -> Inno kur -> `python build_installer.py` (özet kapısı dahil) -> `gh release create --verify-tag` |

Windows'a özgü testler (`build_verify`, kayıt defteri) `winreg` / `subprocess` taklitleriyle yazıldığı için `test.yml` Linux'ta da geçer.
