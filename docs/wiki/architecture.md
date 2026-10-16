# Sistem Mimarisi ve Tasarım Prensipleri

Bu sayfa, P021-OCR masaüstü uygulamasının genel katmanlarını, tasarım desenlerini ve bileşenler arası iletişim modelini tanımlar.

İlgili sayfalar: [[ocr_engines]], [[image_processing]], [[exporters]], [[deployment]], [[rules]]

---

## 1. Katmanlı Mimari (Layered Architecture)

Uygulama 4 temel katmana ayrılmıştır:

1. **Giriş ve Yaşam Döngüsü Katmanı (`src/main.py`):**
   - Frozen (PyInstaller `.exe`) ve Development çalışma modlarını otomatik çözer (`_resolve_base_path`).
   - Yüksek DPI ekran ölçekleme ayarlarını (`PassThrough`) etkinleştirir.
   - QApplication ve Fusion dark stil temasını ([[architecture#temalandirma]]) başlatır.

2. **Arayüz Katmanı (`src/ui/`):**
   - **`MainWindow` (`main_window.py`):** Ana pencere orkestratörü. Sol panel (tuval ve filtre kontrolleri) ile sağ panel (metin editörü) arasındaki senkronizasyonu yönetir.
   - **`ImageCanvas` (`components/image_canvas.py`):** `QGraphicsView` tabanlı, akıcı zoom, pan ve etkileşimli ROI (`InteractiveCropRect`) kırpma alanı sunan görüntüleme bileşeni.
   - **`FilterPanel` (`components/filter_panel.py`):** OpenCV önişleme filtre seçeneklerini sunar ve durum değişimlerini `filters_changed` sinyaliyle iletir.
   - **`TextEditorPanel` (`components/text_editor.py`):** OCR çıktılarını gösteren, anlık kelime/karakter istatistikleri tutan ve çoklu dışa aktarım butonlarını barındıran metin paneli.
   - **`OCRWorkerThread` (`workers/ocr_worker.py`):** Ağır OCR tanıma işlemlerini arayüzü dondurmadan arka planda çalıştıran asenkron `QThread` işçisi.

3. **İş Mantığı ve Bilgisayarlı Görü Katmanı (`src/core/`):**
   - **[[image_processing]]:** Görüntü yükleme, dönüştürme, gürültü temizleme ve açı düzeltme statik boru hattı.
   - **[[ocr_engines]]:** OCR motorlarını strateji ve fabrika desenleriyle yöneten çekirdek.

4. **Yardımcı Servisler ve Dışa Aktarıcılar (`src/utils/`):**
   - **[[exporters]]:** TXT, Word (.docx) ve PDF formatlarında belge üretim stratejileri.

---

## 2. Tasarım Desenleri (Design Patterns)

### Strateji Deseni (Strategy Pattern)
- `IOCREngine` ([[ocr_engines]]): Tüm OCR sağlayıcıları (`EasyOCREngine`, `TesseractEngine`) bu soyut taban sınıfı uygular.
- `IDocumentExporter` ([[exporters]]): Belge çıktı formatları (`TxtExporter`, `DocxExporter`, `PdfExporter`) tek arayüz üzerinden işletilir.

### Fabrika Deseni (Factory Pattern)
- `OCREngineFactory`: Motor adından (`"easyocr"`, `"tesseract"`) bağımsız örnek üretir.
- `ExporterFactory`: Format uzantısından (`"txt"`, `"docx"`, `"pdf"`) uygun dışa aktarıcıyı döndürür.

---

## 3. Asenkron İşlem Modeli (Qt Signals & Slots)

```
[MainWindow] --(start_ocr_process)--> [OCRWorkerThread (QThread)]
                                                |
                                    (extract_text arka planda)
                                                |
[MainWindow] <--(result_ready / error_occurred)--
```
Ana UI thread'in kilitlenmesini önlemek için OCR motoru çağrıları daima `OCRWorkerThread` içinde koşturulur.
