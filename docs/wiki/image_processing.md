# Görüntü Önişleme Boru Hattı (OpenCV & NumPy)

Bu sayfa, OCR öncesi görsel netleştirme, gürültü giderme ve açı düzeltme boru hattını tanımlar.

İlgili sayfalar: [[architecture]], [[ocr_engines]]

---

## 1. Unicode Uyumlu Görsel Yükleme

Windows ortamında dosya yollarında Türkçe veya özel karakterler (`ı, ş, ğ, ö, ü, ç`) bulunduğunda `cv2.imread` sessizce `None` döner. Bu hatayı önlemek için:

```python
# np.fromfile + cv2.imdecode ile güvenli okuma
data = np.fromfile(file_path, dtype=np.uint8)
img = cv2.imdecode(data, cv2.IMREAD_COLOR)
```
Bu yöntem dosya yolunu byte dizisi olarak okuyarak karakter kümesi uyumsuzluğunu tamamen ortadan kaldırır.

---

## 2. Filtreleme Boru Hattı Aşamaları ve Sıralaması

`ImageProcessor` (`src/core/processing/image_processor.py`) sınıfında statik olarak tanımlanmış metotlar ve `MainWindow.apply_image_filters` içindeki çalışma sırası:

1. **Akıllı Renk/Paint Karalama Silme ve Harf Onarımı (`remove_color_annotations`, `_build_scribble_mask`):**
   - Windows ClearType alt-piksel (subpixel) kenar yumuşatmalarını yanlışlıkla silmemek için hem HSV doygunluğu (`S >= 150..165`) hem gerçek RGB kroma farkı (`max(R,G,B) - min(R,G,B) >= 100..120`) hem de Bağlantılı Bileşen Analizi (`cv2.connectedComponentsWithStats`, boyut `> 20px`) birlikte uygulanır.
   - Tespit edilen ince MS Paint çizgileri, çapraz karalamalar, dikdörtgen ve daire şekilleri üzerinde **Fast Marching Telea Inpainting (`cv2.inpaint(..., INPAINT_TELEA)`)** ve polariteye duyarlı **Dikey Morfolojik Harf Gövdesi Köprüleme (`MORPH_RECT (1, 5)`)** uygulanarak çizginin kestiği harf bacakları onarılır. Kalın dolgulu renk blokları ise temiz arka plana (`255`) dönüştürülür.
2. **Açı Düzeltme (`deskew`):**
   - Piksel yoğunluğu filtrelerinden önce geometrik hizalama yapar.
   - Otsu eşikleme + yatay morfolojik genişletme (`MORPH_RECT (25, 3)`) ile harfleri satır bloklarına bağlar ve `cv2.HoughLinesP` (OpenCV 4/5 uyumlu) ile `[-25°, +25°]` aralığındaki satırların medyan eğim açısını bulur. Beyaz kenar dolgusu (`BORDER_CONSTANT = 255`) ile döndürür.
3. **Gürültü Temizleme (`denoise`):**
   - `cv2.fastNlMeansDenoising` (`h=8.0`) ile Türkçe noktalı harfleri (`i, ı, ö, ü, ş, ç, ğ`) aşındırmadan arka plan kumlanmasını temizler.
4. **Kontrast İyileştirme (`enhance_contrast`):**
   - CLAHE (Contrast Limited Adaptive Histogram Equalization) uygular. Soluk veya dengesiz aydınlatılmış metinlerin yerel kontrastını dengeler.
5. **Gri Tonlama (`to_grayscale`):**
   - 3 kanallı BGR görseli tek kanallı gri seviyesine indirir.
6. **Çözünürlüğe Duyarlı Adaptif İkilileştirme (`binarize_adaptive`):**
   - Sabit küçük blok boyutu yerine görselin kısa kenarına orantılı (`min_dim // 16`, `[15, 51]` aralığında tek sayı) dinamik `block_size` hesaplayarak yüksek çözünürlüklü görsellerde harflerin içinin boşalmasını (hollow characters) önler.
7. **OCR Ön Hazırlık (`prepare_for_ocr`, `sharpen`, `add_border_padding`):**
   - Küçük kırpımları (`< 160px`) veya geniş fakat alçak şerit/banner ekran görüntülerini (`w >= 500` ve `h < 360`) `INTER_CUBIC` ile 2x büyütür, doğal arka plan rengiyle uyumlu `16px` çerçeve (`add_border_padding`) ekler.

