# Kronolojik Değişiklik Günlüğü (Wiki Log)

Bu dosya, projedeki mimari kararların, kaynak içeri alımlarının (ingest), kod inceleme ve refactoring işlemlerinin kronolojik kayıt defteridir. Yeni kayıtlar dosyanın **en üstüne** eklenir.

---

## [2026-10-17] [REFACTOR] | Sürgülü Ekran Ayracı (QSplitter) Kaldırıldı, Simetrik 1:1 Düzen Kuruldu
- `MainWindow.init_ui`: İki panel arasındaki sürüklenebilir `QSplitter` ve sürgü/tutamak kaldırıldı.
- `QHBoxLayout`: Sol panel (resim önizleme, filtreler, OCR çalıştırma) `stretch=1` ve sağ panel (çıktı metin editörü) `stretch=1` olarak yerleştirilerek ekranın tam ortasından %50 - %50 simetrik olarak ikiye bölünmesi sağlandı.
- `FilterPanel`: Grup kutusu kenar boşlukları (`GROUP_MARGIN_HORIZ = 12`, `GROUP_MARGIN_TOP = 16`) ve QSS başlık ofseti (`left: 10px`) verilerek filtre kutularının ve başlığın sol kenardan kesilmesi önlendi.
- `tests/test_ui_components.py`: Simetrik 1:1 `QHBoxLayout` yapısı ve QSplitter'sız düzen test kapsamına alındı (45/45 test başarılı, `verify.py` sıfır bulgu).
- Wiki'de [[ui_system]] güncellendi.

## [2026-10-17] [FIX] | Pencere Boyutlandırma Uyarlaması Kaldırıldı, Genişlik +15px ve Minimum Boyut Sabitlendi
- `MainWindow.center_on_screen`: Ekran boyutuna göre pencere boyutunu dinamik olarak küçülten `SCREEN_MARGIN_RATIO` uyarlaması kaldırıldı.
- `DEFAULT_WINDOW_WIDTH`: Motor seçme listesindeki ve sol paneldeki daralma/kesilmeyi engellemek için ana pencere genişliği 15 piksel artırılarak `1280` -> `1295` piksele çıkarıldı (`1295x800`).
- `MainWindow.setMinimumSize`: Başlangıç boyutu olan `1295x800` aynı zamanda minimum küçültme boyutu olarak sabitlendi; pencerenin başlangıç boyutundan daha küçük boyutlara daraltılması ve arayüz elemanlarının kesilmesi engellendi.
- `MainWindow.cmb_engine`: Minimum genişliği 210 piksele yükseltildi ve `AdjustToContents` boyutsal uyum politikası verilerek `"EasyOCR (Derin Öğrenme)"` ve `"PyTesseract (Hızlı Çevrimdışı)"` metinlerinin sağ parantez veya son kısımlarının kesilmesi tamamen giderildi.
- `tests/test_ui_components.py`: 1295x800 başlangıç/minimum boyutları ve 210px combobox genişliği test kapsamına alındı (45/45 test başarılı, `verify.py` sıfır bulgu).
- Wiki'de [[ui_system]] güncellendi.

- `ImageProcessor.remove_color_annotations` & `_build_scribble_mask`: ClearType alt-piksel yumuşatmalarını koruyan hibrit HSV doygunluk + RGB kroma + Bağlantılı Bileşen Analizi (`connectedComponentsWithStats`) filtresi kuruldu. MS Paint ile çizilen yatay/çapraz çizikler, dikdörtgen ve daire şekilleri Fast Marching Telea Inpainting (`cv2.inpaint`) ve polariteye duyarlı dikey morfolojik harf gövdesi köprüleme (`MORPH_RECT (1, 5)`) ile onarıldı.
- `ImageProcessor.prepare_for_ocr`: Alçak yükseklikli geniş ekran şeritleri (`w >= 500, h < 360`) için otomatik `2x` `INTER_CUBIC` büyütme eklendi.
- `TesseractEngine`: Çok sütunlu ve afişli görsellerde (`sample6_movie_info.png`) afiş yüzünü metin sanma hatasını gidermek üzere `--oem 3 --psm 3` otomatik sayfa segmentasyonuna geçildi; düşük güvenli ikon/sembol gürültü filtresi (`_is_low_conf_noise`) eklendi.
- `EasyOCREngine`: Video oynatıcı arayüz ikonlarından kaynaklanan düşük olasılıklı (`< 0.20` veya alfanümerik olmayan `< 0.45`) kutular filtrelendi.
- `REAL_TEST`: Yeni eklenen `sample5_video_player.png`, `sample6_movie_info.png` ve MS Paint ile karalanmış/şekil çizilmiş/eğik açık kaynak test görselleri (`sample7`, `sample8`, `sample9`) dahil 9 senaryo x 2 motor = 18 OCR koşumu çalıştırıldı; temizlenmiş görseller ve 54 adet TXT/PDF/DOCX çıktısı `REAL_TEST/exports/` altına üretildi.
- Birim test sayısı 45'e çıkarıldı (45/45 başarılı) ve `verify.py` sıfır yeni bulgu ile doğrulandı.

## [2026-10-17] [FIX] | Gerçek Test Bulguları ve Doğruluk Optimizasyonları (Polarity, Token Joining, Padding)
- `ImageProcessor`: Doğal arka plan rengi tespiti (`get_background_color`), koyu tema tespiti (`is_dark_image`) ve ters polarite normalizasyonu (`invert_if_dark`) eklendi. Yapay beyaz kenar dolgusu yerine görselin gerçek arka plan rengine uyumlu kenar dolgusu yapıldı.
- `EasyOCREngine`: CRAFT ince çizgi tespit eşikleri (`low_text=0.25, link_threshold=0.30, text_threshold=0.40`) optimize edilerek kod tanımlayıcılarındaki (`_`, `.`, `/`) karakter kayıpları giderildi.
- `EasyOCREngine._join_line_tokens`: Nokta, alt çizgi ve eğik çizgi ile biten/başlayan veya boşluğu 4px altındaki kutular için akıllı birleştirme eklendi (`MainWindow.center_on_screen`, `tests/test_ui_components.py` bütünlüğü sağlandı).
- `TesseractEngine`: Koyu tema görselleri için otomatik `invert_if_dark` ters çevirme eklenerek Türkçe karakter bozulmaları giderildi; stray UI icon temizleyicisi (`_is_stray_glyph`) ile `#&` ve `@` artefaktları ayıklandı.
- `REAL_TEST`: 4 adet gerçek ekran görüntüsü üzerinde uçtan uca çalıştırıldı ve `REPORT.md` güncellendi.

## [2026-10-17] [FIX] | Pencere Ekran Dışı Başlatma Hatası Giderildi (Ekran Ortalama)
- `MainWindow` sınıfına `center_on_screen` ve `showEvent` entegre edildi.
- Görev çubuğu hariç net masaüstü alanı (`availableGeometry`) sorgulanarak pencere boyutu ekran boyutunun %88'ini aşmayacak şekilde sınırlandırıldı ve ekranın tam merkezine konumlandırıldı (`self.move(x, y)`).
- `test_main_window_centering` birim testi eklendi (42/42 test başarılı).
- Wiki'ye [[ui_system]] altına ekran ortalama mimarisi işlendi.

## [2026-10-17] [ENHANCE] | OCR Algoritmaları, 2B Satır Sıralama ve Görüntü Önişleme Boru Hattı İyileştirildi
- `OCREngineFactory` içine Singleton önbellekleme (`_instances`) eklendi; her OCR işleminde PyTorch modelinin yeniden yüklenmesi engellendi.
- `EasyOCREngine` içine otomatik CUDA GPU tespiti (`_detect_gpu`), 2B koordinat tabanlı satır kümeleme (`_group_boxes_into_lines`) ve kontrast parametre optimizasyonu eklendi.
- `TesseractEngine` çift okuma (`image_to_string` + `image_to_data`) darboğazı giderildi; `--oem 3 --psm 6` ile tek geçişli yapısal satır ve güven skoru çıkarımına (`_parse_tesseract_data`) geçildi.
- `ImageProcessor` içinde OpenCV 5.x uyumlu Hough Line tabanlı `deskew`, doygunluk (HSV) tabanlı `remove_color_annotations`, çözünürlüğe duyarlı `binarize_adaptive` ve OCR öncesi otomatik büyütme/keskinleştirme/kenar boşluğu (`prepare_for_ocr`, `sharpen`, `add_border_padding`) algoritmaları devreye alındı.
- `MainWindow.apply_image_filters` içinde geometrik `deskew` adımı, gürültü ve kontrast filtrelerinin önüne alındı.
- Birim test sayısı 41'e çıkarıldı ve `verify.py` sıfır yeni bulgu ile doğrulandı.

## [2026-10-17] [REFACTOR] | Merkezi UI Metin ve İkon Mimarisi Kuruldu (Emoji Temizliği)
- Arayüzdeki tüm hardcoded metinler ve emojiler (`📁`, `🚀`, `✨`, `📋`, `📄`, `📘`, `📕`, `🔄`) temizlendi.
- `src/ui/strings.py` (`UIStrings`): Merkezi metin ve bildirim tek doğruluk kaynağı (Single Source of Truth) oluşturuldu.
- `src/ui/icons.py` (`IconProvider`): `QStyle.StandardPixmap` tabanlı platform-native ikon sağlayıcısı kuruldu.
- `MainWindow`, `FilterPanel` ve `TextEditorPanel` yeni mimariye refactor edildi.
- `tests/test_ui_system.py` ile emojisinlik ve ikon geçerliliği test kapsamına alındı (37 test tamamı başarılı).
- Wiki'ye [[ui_system]] sayfası eklendi.

## [2026-10-17] [STABILIZE] | Kritik Sistem Sağlamlaştırma ve Güvenlik Adımları Tamamlandı
- `MainWindow.closeEvent` eklendi; pencere kapatılırken `OCRWorkerThread` güvenli sonlandırma (graceful interruption) sağlandı.
- `src/main.py` içine merkezi formatlı `logging.basicConfig` eklendi.
- `ocr_app.spec` paketleme dosyasına PDF exporter ve PySide6 modülleri (`hiddenimports`) kaydedildi.
- `.github/workflows/test.yml` içine Linux ortamında GUI çökmesini engelleyen `QT_QPA_PLATFORM: offscreen` eklendi.
- `ImageProcessor.load_image` fonksiyonuna 50 MB dosya ve 8000x8000 piksel bellek taşması (decompression bomb) korumaları eklendi.
- `TesseractEngine` içine Windows'ta standart kurulum dizinlerini (`Program Files\Tesseract-OCR`) otomatik tespit mekanizması eklendi.

## [2026-10-17] [INIT] | LLM Wiki Altyapısı Kuruldu
Projede kalıcı bilgi tabanını yönetmek üzere `docs/wiki/` yapısı (`rules.md`, `index.md`, `log.md`, `architecture.md`, `ocr_engines.md`, `image_processing.md`, `exporters.md`, `deployment.md`) ve `CLAUDE.md` oluşturuldu.

## [2026-10-17] [REFACTOR] | Dalga 0-6 Görevleri ve Kalite Düzeltmeleri
- Python 3.10 sanal ortamı kuruldu, bağımlılıklar tam sürümlere sabitlendi.
- PySide6 tabanlı `PdfExporter` geliştirildi ve test paketine entegre edildi.
- `image_canvas.py` yutulan hata (`except Exception: pass`) logger ile giderildi.
- 13 adet kullanılmayan import temizlendi.
- GitHub Actions CI test iş akışı eklendi.
- Test kapsamı %30 hedefini aşacak şekilde 33 birim teste genişletildi.
- `init_ui` ve `extract_text` 50+ satır karmaşıklık eşiğini aşan fonksiyonları parçalandı.
