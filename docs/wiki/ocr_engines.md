# OCR Motorları ve Fabrika Mimarisi

Bu sayfa, metin tanıma motorlarının entegrasyonunu, dil eşleme modellerini ve soyutlama sözleşmesini açıklar.

İlgili sayfalar: [[architecture]], [[image_processing]], [[exporters]]

---

## 1. Soyutlama Arayüzü: `IOCREngine`

Tüm OCR motorları `src/core/interfaces/ocr_interface.py` içindeki `IOCREngine` soyut sınıfını ve `OCRResult` veri modelini uygular.

```python
@dataclass
class OCRResult:
    text: str = ""
    confidence: float = 0.0
    processing_time: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error_message: str = ""
```

---

## 2. Desteklenen Motorlar

### 2.1 EasyOCR Motoru (`EasyOCREngine`)
- **Dosya:** `src/core/engines/easyocr_engine.py`
- **Model:** PyTorch tabanlı derin öğrenme (CRAFT algılama + CRNN tanıma modelleri).
- **Otomatik GPU Algılama:** `_detect_gpu()` ile `torch.cuda.is_available()` kontrol edilerek varsa CUDA hızlandırma otomatik etkinleştirilir.
- **2B Akıllı Satır Birleştirme (`_group_boxes_into_lines`):** Algılanan metin kutularını dikey merkez (`y_center`) ve satır yüksekliği (`height * 0.55`) toleransına göre yatay satırlara kümelendirir; her satır içindeki kelimeleri soldan sağa (`x_min`) sıralayarak birleştirir.
- **Ön Hazırlık ve Parametre Optimizasyonu:** OCR öncesi `ImageProcessor.prepare_for_ocr()` ile küçük kırpımlar 2x büyütülüp keskinleştirilir ve beyaz kenar boşluğu eklenir; `contrast_ths=0.1, adjust_contrast=0.5` ile düşük kontrastlı Türkçe karakterlerin algılanması iyileştirilir.

### 2.2 PyTesseract Motoru (`TesseractEngine`)
- **Dosya:** `src/core/engines/tesseract_engine.py`
- **Model:** Geleneksel OCR motoru (Google Tesseract OCR binary, `--oem 3 --psm 6` LSTM modu).
- **Tek Geçişli Çıkarım (`_parse_tesseract_data`):** Yalnızca tek bir `image_to_data` çağrısı ile hem `(block_num, par_num, line_num)` hiyerarşisine göre satır bazlı metin hem de kelime bazlı güven skoru ve `bbox` detayları aynı anda çıkarılır (çift okuma maliyeti ortadan kaldırılmıştır).
- **Gereksinim:** Sistemde Tesseract ikili dosyasının kurulu olması gereklidir (`Program Files\Tesseract-OCR` otomatik algılanır).

---

## 3. Motor Fabrikası ve Önbellekleme: `OCREngineFactory`

- **Dosya:** `src/core/factories/ocr_factory.py`
- **Singleton / Instance Caching (`_instances`):** `get_engine(key)` çağrıldığında oluşturulan motor nesnesi `_instances` sözlüğünde önbelleğe alınır. Böylece her OCR işleminde PyTorch model ağırlıklarının diskten RAM'e tekrar yüklenmesi engellenir.
- **Dinamik Kayıt:** `register_engine(key, engine_cls)` metodu sayesinde yeni motorlar runtime'da sisteme eklenebilir ve ilgili önbellek otomatik yenilenir.

---

## 4. Tarama Stratejileri ve Bölgesel Düzen Analizi (`IScanStrategy` & `XYCutLayoutAnalyzer`)

Akış şemaları, çok sütunlu makaleler ve yan yana kartlarda klasik satır kümeleme algoritmaları aynı yatay eksendeki ($Y$ koordinatı) bağımsız metinleri birbirine karıştırır (`"Fiyat Duygu Risk Portföy / Tahmini Analizi Profili Optimizasyonu"`). Bunu çözmek için tak-çıkar strateji mimarisi eklenmiştir:

### 4.1 XY-Cut ve 2B Uzamsal Blok Analizi (`XYCutLayoutAnalyzer`)
- **Dosya:** `src/core/layout/xy_cut_analyzer.py`
- Bounding box'lar arasındaki dikey (`SAME_LINE_V_OVERLAP_RATIO = 0.45`) ve yatay boşlukları (`SAME_COL_H_OVERLAP_RATIO = 0.40`, `SAME_COL_MAX_V_GAP_RATIO = 0.90`) tarar.
- Komşuluk grafiği (`_build_adjacency_graph`) ve BFS bileşen dolaşımı (`_traverse_component`) ile bağımsız kartları/sütunları ayrı görsel kümelere ayırır.
- Kümeleri satır bazlı kuantize $Y$ seviyesi ve $X$ koordinatına göre doğal hiyerarşik okuma sırasına (Reading Order) dizer (`[1. Bölge]`, `[2. Bölge]`, ...).

### 4.2 Tak-Çıkar Tarama Modları (`ScanStrategyFactory`)
- **Düz Metin (Satır Satır) - `LineScanStrategy`:** Kitap, makale ve düz metinler için standart tek sütunlu satır taraması.
- **Bölgesel / Şema (Blok Blok) - `BlockScanStrategy`:** Akış şemaları, tablolar, sunumlar ve kartlar için otomatik blok ayrıştırma.
- **Seçili Alanlar (Çoklu Bölge) - `MultiRegionStrategy`:** Tuvalde kullanıcının Shift ile seçtiği çoklu ROI alanlarını sırayla tarayıp birleştirir.
