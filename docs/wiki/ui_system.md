# Merkezi Kullanıcı Arayüzü Sistemi (UIStrings & IconProvider)

Bu sayfa, arayüzdeki metinlerin (strings) ve ikonların (icons) merkezi yönetim modelini açıklar.

İlgili sayfalar: [[architecture]], [[rules]]

---

## 1. Neden Emoji Kullanılmıyor?

Masaüstü uygulamalarında doğrudan metinlerin içerisine emoji (`📁`, `🚀`, `✨`, `📋`, `📄`) yerleştirmek aşağıdaki teknik sorunlara yol açar:
1. **İşletim Sistemi Tutarsızlığı:** Windows sürümleri arasında renkli emoji desteği ve font render glifleri farklılık gösterir; bazı kurumsal Windows sürümlerinde kutu (`□`) veya okunaksız semboller olarak görünür.
2. **Çoklu Dil (Localization / i18n) İmkansızlığı:** Hardcoded metinler ve emojiler kod tabanına dağıldığında uygulamanın başka bir dile çevrilmesi imkansızlaşır.
3. **Erişilebilirlik ve Kurumsal Görünüm:** Ekran okuyucularda (screen reader) emojiler anlam karmaşası yaratır.

---

## 2. Merkezi Metin Yönetimi (`UIStrings`)

- **Dosya:** `src/ui/strings.py`
- **Tasarım:** Single Source of Truth (Tek Doğruluk Kaynağı).
- **Örnek Kullanım:**
```python
from src.ui.strings import UIStrings

btn_open = QPushButton(UIStrings.BTN_OPEN_IMAGE)
self.lbl_status.setText(UIStrings.STATUS_SUCCESS.format(time=1.2, confidence=95.4))
```

---

## 3. Merkezi İkon Sağlayıcı (`IconProvider`)

- **Dosya:** `src/ui/icons.py`
- **Tasarım:** Enum tabanlı `IconType` ve `IconProvider.get_icon(icon_type)`.
- **Motor:** Harici ağır resim dosyaları paketlemek yerine işletim sisteminin native `QStyle.StandardPixmap` vektör motorunu kullanır.

```python
from src.ui.icons import IconProvider, IconType

btn_open.setIcon(IconProvider.get_icon(IconType.OPEN_IMAGE))
btn_run.setIcon(IconProvider.get_icon(IconType.RUN_OCR))
btn_reset.setIcon(IconProvider.get_icon(IconType.RESET_FILTERS))
```

---

## 4. Ekran Ortalama ve Minimum Boyut Mimarisi (`center_on_screen`)

- **Dosya:** `src/ui/main_window.py`
- **Tasarım:** Arayüz bileşenlerinin (motor seçme listesi, filtreler, panel butonları) daralma/sıkışma nedeniyle metinlerinin kesilmesini engellemek için dinamik pencere küçültme uyarlaması kaldırılmıştır.
- **Çözüm:**
  - **Başlangıç ve Minimum Boyut:** Ana pencere genişliği 15 piksel artırılarak `1295x800` px olarak sabitlenmiştir (`DEFAULT_WINDOW_WIDTH = 1295`, `DEFAULT_WINDOW_HEIGHT = 800`).
  - **Minimum Küçültme Sınırı:** `self.setMinimumSize(1295, 800)` tanımlanarak kullanıcının pencereyi başlangıç boyutundan daha küçük boyutlara küçültmesi ve arayüz elemanlarının kesilmesi engellenmiştir (pencere büyütülebilir veya tam ekran yapılabilir).
  - **Motor Seçim Alanı (`cmb_engine`):** Minimum genişlik 210 piksele çıkarılmış ve `AdjustToContents` politikası uygulanarak `"EasyOCR (Derin Öğrenme)"` ve `"PyTesseract (Hızlı Çevrimdışı)"` metinlerinin sağ parantez veya son harflerinin kesilmesi önlenmiştir.
  - **Ekran Ortalama:** `screen.availableGeometry()` sorgulanarak pencere hem `__init__` aşamasında hem de ilk `showEvent` anında masaüstü alanının tam merkezine (`self.move(x, y)`) konumlandırılır.

---

## 5. Simetrik 1:1 Düzen ve QSplitter'ın Kaldırılması

- **Dosya:** `src/ui/main_window.py`
- **Tasarım:** Arayüzün ortasındaki sürgü / kaydırma tutamağı (`QSplitter` handle dots) ve panellerin orantısız daralması engellenmiştir.
- **Çözüm:**
  - `QSplitter` tamamen kaldırılmış, yerine native `QHBoxLayout` kullanılmıştır.
  - Sol panel (Resim önizleme, filtreler ve OCR kontrolleri) `stretch=1`, sağ panel (Ayrıştırılan metin çıktısı ve dışa aktarım butonları) `stretch=1` olarak yerleştirilmiştir.
  - Böylece arayüz ekranın tam ortasından simetrik (%50 sol, %50 sağ) olarak ikiye bölünmüş, kaydırma/sürgü aracı olmadan sabit ve dengeli bir görünüm elde edilmiştir.

---

## 6. Tak-Çıkar Tuval Katmanı ve Tıklanabilir Kutu Panoya Kopyalama (`CanvasOverlayManager`)

- **Dosya:** `src/ui/components/overlay_manager.py`
- **Tasarım:** Tak-Çıkar (Loosely Coupled) Overlay Mimarisi. `ImageCanvas` çekirdek mantığına dokunmadan `QGraphicsScene` üzerine dinamik etkileşim katmanı ekler.
- **Yetenekler:**
  - **Tıklanabilir Kutu (`ClickableBoxItem`):** OCR sonucu dönen her kelime/blok kutusu yarı şeffaf yeşil renkle vurgulanır.
  - **Hover Glow:** Fare kutu üzerine geldiğinde çerçeve beyaz parlamaya dönüşür ve metin ile güven skorunu gösteren tooltip açılır.
  - **Tıkla-Kopyala (Click-to-Copy):** Kutuya sol tıklandığında içindeki metin anında işletim sistemi panosuna (`QGuiApplication.clipboard()`) kopyalanır ve alt durum çubuğunda bildirim gösterilir.
  - **Görünürlük Kontrolü (`chk_overlay`):** Kullanıcı "Metin Kutularını Göster" onay kutusu ile kutu katmanını istediği an açıp kapatabilir.
  - **Çoklu ROI Alanı Seçimi:** Tuval üzerinde Shift tuşuna basılı tutularak birden fazla alan seçilebilir, sağ tıklandığında seçimler temizlenir.

## 7. OCR Akışı Koordinat ve Dayanıklılık Kuralları (`MainWindow.start_ocr_process`)

- **Tek ROI / tam görsel (`line`, `block`):** Worker'a seçili ilk bölgenin kırpımı verilir; sonuç kutuları `ImageCanvas.get_primary_region_offset()` ofsetiyle `ImageProcessor.shift_details_coordinates` üzerinden tam görsel uzayına çevrilip tuvale çizilir.
- **Çoklu bölge (`multi_region`):** Strateji bölgeleri görsel koordinatlarında tuttuğu için worker'a kırpım değil `ImageCanvas.get_full_cv_image()` (tam görsel) verilir; `MultiRegionStrategy` her bölgeyi kendisi keser ve kutuları ofsetler.
- **`CanvasOverlayManager.clear()`:** `QGraphicsScene.clear()` (yeni görsel/filtre) öğelerin C++ nesnesini zaten sildiği için `removeItem` çağrısı `RuntimeError` yakalanarak güvenli yapıldı; aksi halde OCR sonrası ikinci OCR, filtre değişimi veya yeni görsel yükleme çöküyordu.
- Testler: `tests/test_main_window_ocr_flow.py`, `tests/test_overlay_manager.py`. Bkz. [[ocr_engines]].

## 8. Yardım Menüsü ve Güncelleme Penceresi
- `MainWindow` menü çubuğunda **Yardım**: `Sürüm X.Y.Z` (pasif), `Güncellemeleri Denetle`, `Açılışta Güncellemeyi Denetle` (işaretli kutu, `~/.ocraraci/updates.json`).
- `UpdateDialog` yalnızca görünümdür (indirme çubuğu, "Windows bekleniyor...", `Beklemeyi Bırak`, `Sürüm Sayfası`, `Bu Sürümü Atla`); mantık `UpdateController`'dadır. Tüm metinler `UIStrings` içindedir. Akış ve güvenlik: [[update_system]].

## 9. Uygulama İkonu
- **Tasarım:** koyu zemin, açık renkli belge (metin satırları) ve etrafında tema yeşili (`#00e676`) tarama çerçevesi + tarama çizgisi. `tools/make_icon.py` Pillow ile üretir (dış dosya yok): `packaging/app_icon.ico` (16/24/32/48/64/128/256 px; exe, Inno kurulum sihirbazı, Başlat menüsü kısayolu ve Gezgin'deki dosya/dizin ikonu) ve `src/ui/assets/app_icon.png` (256 px; pencere ve görev çubuğu).
- **Çalışma zamanı:** `IconProvider.get_app_icon()` PNG'yi yükler; `main.py` `app.setWindowIcon(...)` ile tüm pencere ve diyaloglara uygular ve `SetCurrentProcessExplicitAppUserModelID` ile görev çubuğunda Python yerine uygulamanın ikonunu gösterir.
- **Paketleme:** `.ico` `--icon` ile exe'ye gömülür (exe özetine girer, [[exe_distribution]]); `src/ui/assets` `--add-data` ile veri dosyası olarak `_internal` altına kopyalanır. Kurulum sihirbazı `SetupIconFile=app_icon.ico` kullanır.
- Testler: `tests/test_ui_system.py` (ikon geçerli, çok boyutlu, ana pencerede var), `tests/test_release_packaging.py` (ico özeti ve boyutları, PyInstaller bayrakları).
