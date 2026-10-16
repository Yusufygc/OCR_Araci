# Dışa Aktarma Mekanizması (Exporters)

Bu sayfa, ayrıştırılan OCR metinlerinin farklı dosya formatlarında kaydedilmesini sağlayan strateji yapısını açıklar.

İlgili sayfalar: [[architecture]], [[ocr_engines]]

---

## 1. Soyutlama Arayüzü: `IDocumentExporter`

`src/utils/exporters/exporter_interface.py` içinde tanımlanır:

```python
class IDocumentExporter(ABC):
    @property
    @abstractmethod
    def file_extension(self) -> str: pass

    @property
    @abstractmethod
    def file_filter(self) -> str: pass

    @abstractmethod
    def export(self, text: str, output_path: str) -> bool: pass
```

---

## 2. Desteklenen Formatlar

### 2.1 TXT Dışa Aktarıcı (`TxtExporter`)
- **Dosya:** `src/utils/exporters/txt_exporter.py`
- **Uzantı:** `.txt`
- **Karakter Kodlaması:** UTF-8 ile düz metin yazımı.

### 2.2 Word Dışa Aktarıcı (`DocxExporter`)
- **Dosya:** `src/utils/exporters/docx_exporter.py`
- **Uzantı:** `.docx`
- **Kütüphane:** `python-docx`
- **Format:** Metin satırlarını paragraflar halinde Word belgesine dönüştürür.

### 2.3 PDF Dışa Aktarıcı (`PdfExporter`)
- **Dosya:** `src/utils/exporters/pdf_exporter.py`
- **Uzantı:** `.pdf`
- **Motor:** `PySide6.QtGui.QPdfWriter` + `QTextDocument`
- **Avantaj:** Harici ağır bir PDF kütüphanesi gerektirmez. Sistem fontlarını kullanarak Türkçe karakterleri (`ğ, ş, ı, İ, ç, ö, ü`) tam uyumla yazdırır.

---

## 3. Fabrika Sınıfı: `ExporterFactory`

`src/utils/exporters/exporter_factory.py`:
- `get_exporter(format_key)`: `"txt"`, `"docx"`, `"pdf"` anahtarlarına göre ilgili exporter nesnesini döndürür.
- `get_file_dialog_filters()`: Qt dosya kaydetme diyaloğunda gösterilecek filtre dizesini dinamik birleştirir.
