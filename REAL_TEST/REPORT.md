# GERÇEK KULLANICI TESTİ, PAINT KARALAMA TEMİZLEME VE OCR KALİTE RAPORU
**Test Tarihi:** 2026-10-17 03:32:29
**Test Klasörü:** `C:\2UYGULAMALAR\P021-OCR\REAL_TEST`

---

### Test Özeti Tablosu (10 Senaryo x 2 Motor = 20 OCR Koşumu)
| Görsel | Motor | Süre (sn) | Güven (%) | Başarı | Anahtar Kelime |
| :--- | :--- | :--- | :--- | :--- | :--- |
| sample1_dark_ui1.png | EasyOCR (Derin Öğrenme) | 3.53s | 81.4% | BAŞARILI | 5/5 |
| sample1_dark_ui1.png | PyTesseract (Hızlı Çevrimdışı) | 1.24s | 87.4% | BAŞARILI | 5/5 |
| sample2_dark_ui2.png | EasyOCR (Derin Öğrenme) | 2.55s | 79.3% | BAŞARILI | 4/5 |
| sample2_dark_ui2.png | PyTesseract (Hızlı Çevrimdışı) | 1.57s | 91.3% | BAŞARILI | 5/5 |
| sample3_search_snippet.png | EasyOCR (Derin Öğrenme) | 1.08s | 87.0% | BAŞARILI | 5/5 |
| sample3_search_snippet.png | PyTesseract (Hızlı Çevrimdışı) | 0.55s | 91.6% | BAŞARILI | 5/5 |
| sample4_wiki_document.png | EasyOCR (Derin Öğrenme) | 3.51s | 79.6% | BAŞARILI | 5/5 |
| sample4_wiki_document.png | PyTesseract (Hızlı Çevrimdışı) | 0.89s | 87.2% | BAŞARILI | 3/5 |
| sample5_video_player.png | EasyOCR (Derin Öğrenme) | 3.15s | 53.9% | BAŞARILI | 3/5 |
| sample5_video_player.png | PyTesseract (Hızlı Çevrimdışı) | 0.56s | 74.9% | BAŞARILI | 4/5 |
| sample6_movie_info.png | EasyOCR (Derin Öğrenme) | 1.93s | 82.8% | BAŞARILI | 5/5 |
| sample6_movie_info.png | PyTesseract (Hızlı Çevrimdışı) | 0.78s | 82.9% | BAŞARILI | 5/5 |
| sample7_paint_scribbles_light.png | EasyOCR (Derin Öğrenme) | 3.27s | 64.1% | BAŞARILI | 4/5 |
| sample7_paint_scribbles_light.png | PyTesseract (Hızlı Çevrimdışı) | 0.86s | 82.0% | BAŞARILI | 5/5 |
| sample8_paint_scribbles_dark.png | EasyOCR (Derin Öğrenme) | 1.81s | 80.2% | BAŞARILI | 5/5 |
| sample8_paint_scribbles_dark.png | PyTesseract (Hızlı Çevrimdışı) | 0.76s | 75.1% | BAŞARILI | 5/5 |
| sample9_opensource_paint_skew.png | EasyOCR (Derin Öğrenme) | 1.10s | 73.7% | BAŞARILI | 5/5 |
| sample9_opensource_paint_skew.png | PyTesseract (Hızlı Çevrimdışı) | 0.45s | 90.4% | BAŞARILI | 5/5 |
| sample10_diagram_clean.png | EasyOCR (Derin Öğrenme) | 0.54s | 78.1% | BAŞARILI | 3/7 |
| sample10_diagram_clean.png | PyTesseract (Hızlı Çevrimdışı) | 0.33s | 76.4% | BAŞARILI | 5/7 |

---

## Görsel: Koyu Tema UI Metni 1 (Dinamik Ekran / Ortalama)
- **Dosya:** `sample1_dark_ui1.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 3.53 saniye
- **Ortalama Güven Skoru:** 81.39%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Dinamik Ekran Boyutu, MainWindow, Merkezine, showEvent, Wiki`)
```text
Yapılan Düzenlemeler:
1. Dinamik Ekran Boyutu ve Görev Çubuğu Uyarlaması:MainWindow.center_on_screen   metodu eklendi. Sabit
1280x800  boyutu, küçük ekranlarda (ör. 1366x768) veya %125-%150 Windows ekran ölçeklemesinde (DPI
scaling) ekran dışına taşmaması için screen.availableGeometry() (görev çubuğu hariç net alan) üzerinden
kontrol edilerek sınırlandırıldı.
2 Ekranın Merkezine Konumlandırma: Pencerenin sol-üst koordinatları hesaplanarak aktif ekranın tam merkezine
taşındı ( self.move(x, y) )
3.İlk Gösterimde Otomatik Ortalama:MainWindow.showEvent   içine tek seferlik tetikleyici eklenerek pencerenin
ilk render anında her zaman ekranın ortasında açılması garanti altına alındı:
4. Test ve Wiki Güncellemesi:tests/test_ui_components.py   içine test eklendi (42/42 test başarılı) ,
verify.py sıfir bulgu ile doğrulandı ve docs/wikilui_system.md ile docs/wiki/log.md güncellendi
files changed +55-3 Review
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 1.24 saniye
- **Ortalama Güven Skoru:** 87.38%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Dinamik Ekran Boyutu, MainWindow, Merkezine, showEvent, Wiki`)
```text
Yapılan Düzenlemeler:
1.Dinamik Ekran Boyutu ve Görev Çubuğu Uyarlaması:MainWindow.center on screen metodu eklendi.Sabit
128ex8ee boyutu, küçük ekranlarda (Gr.1366x768) veya %125-%150 Windows ekran dlceklemesinde (DPI
scaling) ekran disina taşmaması icin screen.availableGeometry() (gérev cubugu harig net alan) Uzerinden
kontrol edilerek sinirlandirildi.
2.Ekranin Merkezine Konumlandirma:Pencerenin sol-iist hesaplanarak aktif ekranin tam merkezine
tasindi self.move(x, y)
3.İlk Gösterimde Otomatik Ortalama:MainWindow.showEvent icine tek seferlik tetikleyici eklenerek pencerenin
ilk render anında her zaman ekranın ortasında açılması garanti altına alındı.
4.Test ve Wiki Güncellemesi:tests/test_ui_components.py icine test eklendi (42/42 test başarılı),
verify.py sifir bulgu ile dogrulandi ve docs/wiki/ui_system.md ile docs/wiki/log.md giincellendi.
4 files changed +55-3 > Review
```

---

## Görsel: Koyu Tema UI Metni 2 (Görüntü Önişleme Adımları)
- **Dosya:** `sample2_dark_ui2.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 2.55 saniye
- **Ortalama Güven Skoru:** 79.29%
- **Anahtar Kelime Eşleşmesi:** 4/5 (`deskew, remove_color_annotations, binarize_adaptive, prepare_for_ocr`)
```text
3. Adım: GörüntüÖnişleme (OpenCV) Algoritmalarının Yenilenmesi
OpenCV 5.x Uyumlu deskew image_processor.py   içinde hatalı  minAreaRect yaklaşımı yerine; yatay
morfolojik satır bağlama ( MORPH_RECT (25, 3) ) + Hough Line Transform ( HoughLinesP ) ile [-25" +25"]
arasındaki gerçek satır açılarını medyan ile hesaplayan_estimate_skew_angle algoritmasına geçildi. Kenar
dolgusu beyaz ( 255 ) yapıldı:
HSV Doygunluk Tabanlı remove_color_annotations :remove_color_annotations artık remove_red ve
remove_blueparametrelerini kullanarak yüksek doygunluklu renkli kalem/fosforlu izlerini temizlerken; siyah/gri
metinlerin yumuşak kenarlarını (anti-aliasing) koruyor.
Çözünürlüğe Duyarlı binarize_adaptive binarize_adaptive içinde sabit block_size-11 yerine görsel
çözünürlüğüne göre dinamik blok boyutu ( [15, 51] aralığında) hesaplanarak büyük görsellerde harflerin içinin
boşalması önlendi.
Otomatik Kenar Boşluğu ve Küçük Metin Büyütme:prepare_for_ocr sharpen   ve
add_border_padding   eklenerek küçük kırpımların ' 160px ) otomatik 2x büyütülüp netlestirilmesi ve etrafına
16px beyaz çerçeve eklenmesi sağlandı.
Boru Hattı Sıralaması:main_window.py içinde geometrik deskew adımı; gürültü ve kontrast filtrelerinin
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 1.57 saniye
- **Ortalama Güven Skoru:** 91.34%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Görüntü Önişleme, deskew, remove_color_annotations, binarize_adaptive, prepare_for_ocr`)
```text
3.Adım:Görüntü Önişleme (OpenCV) Algoritmalarının Yenilenmesi
* OpenCV 5.x Uyumlu deskew:image_processor.py içinde hatalı minAreaRect yaklaşımı yerine, yatay
morfolojik satır bağlama MORPH RECT (25, 3) Hough Line Transform HoughLinesP ile [-25°, +25°]
arasındaki gerçek satır açılarını medyan ile hesaplayan_estimate_skew_angle algoritmasına geçildi.Kenar
dolgusu beyaz 255 yapıldı.
* HSV Doygunluk Tabanlı remove color annotations remove_color_annotations artik remove_red ve
remove blue parametrelerini kullanarak yüksek doygunluklu renkli kalem/fosforlu izlerini temizlerken, siyah/gri
metinlerin yumuşak kenarlarını (anti-aliasing) koruyor.
Çözünürlüğe Duyarlı binarize adaptive binarize_adaptive içinde sabit block_size=11 yerine görsel
çözünürlüğüne göre dinamik blok boyutu (15, 51] aralığında) hesaplanarak büyük görsellerde harflerin içinin
boşalması önlendi.
Otomatik Kenar Boşluğu ve Küçük Metin Büyütme:prepare_for_ocr sharpen ve
* add border padding eklenerek küçük kırpımların 16@px otomatik 2x büyütülüp netleştirilmesi ve etrafına
16px beyaz çerçeve eklenmesi sağlandı.
* Boru Hattı Sıralaması:main window.py icinde geometrik deskew adımı, gürültü ve kontrast filtrelerinin
```

---

## Görsel: Arama Sonucu Snippet (Film/Dizi Başlığı & Açıklama)
- **Dosya:** `sample3_search_snippet.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 1.08 saniye
- **Ortalama Güven Skoru:** 86.96%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Film izle Hell, Soulm8te, Türkçe Dublaj, yapay zekayı, kaos`)
```text
8 Film izle Hell
https Jhilmizlehell net > Filmler
Soulm8te Türkçe Dublaj izle (2026)
Soulm8te izle: Şirketi elinden alınan kederli mühendis; test ettiği yapay zekayı bilinçli bir ruh eşi
yapmaya çalısırken; bu durum amansız bir kaos
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.55 saniye
- **Ortalama Güven Skoru:** 91.57%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Film izle Hell, Soulm8te, Türkçe Dublaj, yapay zekayı, kaos`)
```text
Film izle Hell
> Filmler
Soulm8te Türkçe Dublaj izle (2026)
izle:Sirketi elinden alinan kederli mihendis, test ettiği yapay zekayı bilinçli bir ruh esi
yapmaya bu durum amansiz bir kaos
```

---

## Görsel: Açık Tema Doküman (Wikipedia Hukuk Metni)
- **Dosya:** `sample4_wiki_document.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 3.51 saniye
- **Ortalama Güven Skoru:** 79.57%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Program çeşitleri, Bankacılık, Vergi Hukuku, Kamu Hukuku, Özel Hukuk`)
```text
Program çeşitleri [değiştir | kaynağı değiştir ]
Genelden baslayarak uzmanlasmaya doğru kademelendirilebilen farklı LLM: programları bulunmaktadır. Yeni programlar ençok
rağbet görenlerdir: Bankacılık ve Finansman Hukuku; Deniz Hukuku; Vergi Hukuku; Rekabet Hukuku bunlara örnek gösterilebilir.
Londra'daki University College London ve Londra Üniversitesi'nde ya da Saarbrücken'deki Saarland Üniversitesi Avrupa Hukuku
Bölümü'nde bu programlar bulunmaktadır.
Türkiye'de ise LLM programları baslıca Kamu Hukuku ve Özel Hukuk ayrımında ele alınıp; çalısılacak konular bu ayrıma tabi alt
dallar kapsamında görülmüstür . Yakın tarihlerde ise, cesitli vakıf üniversitelerinde İnsan Hakları alanında yüksek lisans programları
açılmış ve bazı üniversitelerin LLM programları hukuk dışında lisans yapmıs öğrencileri de kabul edilmiştir.
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.89 saniye
- **Ortalama Güven Skoru:** 87.19%
- **Anahtar Kelime Eşleşmesi:** 3/5 (`Program çeşitleri, Vergi Hukuku, Kamu Hukuku`)
```text
Program çeşitleri | değiştir | kaynağı değiştir
Genelden başlayarak uzmanlaşmaya doğru kademelendirilebilen farklı LL.M.programları bulunmaktadır.Yeni programlar en cok
ragbet gorenlerdir:Bankacilik ve Finansman Hukuku, Deniz Hukuku, Vergi Hukuku, Rekabet Hukuku bunlara örnek g6sterilebilir.
Londra'daki University College London ve Londra Universitesi'nde ya da Saarbriicken'deki Saarland Universitesi Avrupa Hukuku
Bolumi'nde bu programlar bulunmaktadir.
Turkiye'de ise LL.M programları baslica Kamu Hukuku ve Ozel Hukuk ayriminda ele alinip, calisilacak konular bu ayrima tabi alt
dallar kapsaminda görülmüştür.Yakin tarihlerde ise, cesitli vakif tiniversitelerinde Insan Haklari alaninda yüksek lisans
acilmis ve bazi Universitelerin LLM programlari hukuk disinda lisans yapmis 6grencileri de kabul edilmistir.
```

---

## Görsel: Koyu Video Oynatıcı Arayüzü ve Alt Banner
- **Dosya:** `sample5_video_player.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 3.15 saniye
- **Ortalama Güven Skoru:** 53.91%
- **Anahtar Kelime Eşleşmesi:** 3/5 (`Altyazılı, Yatırım, Turnuvalar`)
```text
Turkçe Dublaj Altyazılı
C 10200 / 1240.10 0 @ # @ /
%100 İlk Yatırım +%100 Kayıp Bonusu; Turnuvalar Ve Daha Fazlası Zlot'ta
2 DEneme
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.56 saniye
- **Ortalama Güven Skoru:** 74.89%
- **Anahtar Kelime Eşleşmesi:** 4/5 (`Türkçe Dublaj, 1:40:10, Yatırım, Turnuvalar`)
```text
r
Türkçe Dublaj | | Atyazih
> $1 102007 1:40:10 Ae
96100 ilk Yatırım +%100 Kayip Bonusu, Turnuvalar Ve Daha Fazlası Zlot'ta
-<A
Denote DO
-
```

---

## Görsel: Afişli Film Bilgi Kartı (Çok Sütunlu Koyu UI)
- **Dosya:** `sample6_movie_info.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 1.93 saniye
- **Ortalama Güven Skoru:** 82.79%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Filminin Bilgileri, teknoloji devi, yapay zeka, 99 dakika, Gerilim`)
```text
Soulm8te Filminin Bilgileri
Büyük bir teknoloji devi şirketini satın alır: Yas tutan mühendis; yeni
yapay zeka programını test etmekle görevlendirilir Fakat yapay zekayı
gerçek bir ruh eşi olacak gekilde programlamaya çalıştığında;
beklenmedik istekler gelistirir ve ortalık karışır
IMDb Puani
Fragman
Süre 99 dakika
izlenme 14,573 izlenme
Yıl - Ülke 2026 ABD
Türler Gerilim Science Fiction Korku
Kategori Filmler 108Op Film izle
'David
S 0 U L M 8 T E Rysdahl
filmleri
Lily Sull_  David R_ Claudia_Arty Fr_Elijah Is_   Mara Huf   Isabelle .
Sara / Lydia David Was.Aubrey Mac Ben Hoffma Terrance Lizzie Circe
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.78 saniye
- **Ortalama Güven Skoru:** 82.91%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Filminin Bilgileri, teknoloji devi, yapay zeka, 99 dakika, Gerilim`)
```text
Soulmste Filminin Bilgileri
Büyük bir teknoloji devi şirketini satın alır.Yas tutan mühendis, yeni
yapay zeka programını test etmekle görevlendirilir.Fakat yapay zekayı,
gerçek bir ruh eşi olacak şekilde programlamaya çalıştığında,
beklenmedik istekler geliştirir ve ortalık karışır.
IMDb Puani
Fragman
5.8
Süre 99 dakika
İzlenme 14,573 izlenme
Yil-lke 2026 ABD
Türler Gerilim Science Fiction Korku
4 Kategori Filmler 1080p Film izle
>
Lk
2 oy
Lily Sull...David R..Claudia...ArtyFr...Elijah Mara Huf
```

---

## Görsel: MS Paint Çizikli & Şekilli Açık Doküman (Kırmızı Çizgi, Mavi Kutu, Yeşil Daire)
- **Dosya:** `sample7_paint_scribbles_light.png` (`Pipeline: clean_paint`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 3.27 saniye
- **Ortalama Güven Skoru:** 64.05%
- **Anahtar Kelime Eşleşmesi:** 4/5 (`Program çeşitleri, Bankacılık, Rekabet Hukuku, Hakları`)
```text
Program çeşitleri [değiştir | kaynağı değiştir ]
Goroldo~ caç ayarak. uzma1 açma'a doğ-J kadc~clo~dirilebilen farklı __I.4. programları bulunmaktadır.  Yeni programlar en çok
rağbet görenlerdir: Bankacılık ve Fnansman Hukuku; Ceniz Hukukı= Vergi Huk_ku; Rekabet Hukuku bunlara örnek gösterilebilir.
Iordra'da< |Iniver:'fy
dallar kapsamında görülmüstür . Yakın tarihlerde ise, cesitli vakıf üniversitelerinde İnsan Hakları alanında yüksek lisans programları
açılmıs ve bazı üniversitelerin LLM programları hukuk dışında lisans yapmıs öğrencileri de kabul edilmistir.
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.86 saniye
- **Ortalama Güven Skoru:** 82.03%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Program çeşitleri, Bankacılık, Rekabet Hukuku, University, Hakları`)
```text
Program çeşitleri | değiştir | kaynağı değiştir
Goroldo” cag ayarak dzman açmaya doğru kade~olodirilebilen farklı.M.programları bulunmaktadır.Yeni programlar en cok
ragbet görenlerdir:Bankacılık ve Fnansman Hukuku, Ceniz Hukukı Vergi Huk.,ku, Rekabet Hukuku bunlara örnek gösterilebilir.
| andra'dax University Callege Landan ve | eadra ya da icken'dek Saarland Universitesi Avrupa Hukuku
Be ümürce bt
Tirkive'ce se L.M bas ca Kanu! Özel lukuk aviminda ele alinip, calisilacak konular bu ayrima tabi alt
dallar kapsaminda görülmüştür.Yakin tarihlerde ise, cesitli vakif iniversitelerinde Insan Hakları alaninda yüksek lisans programlari
acilmis ve bazi Universitelerin LLM programlari hukuk disinda lisans yapmis 6Grencileri de kabul edilmistir.
```

---

## Görsel: MS Paint Çizikli & Şekilli Koyu Film Kartı (Renkli Karalama & Şekiller)
- **Dosya:** `sample8_paint_scribbles_dark.png` (`Pipeline: clean_paint`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 1.81 saniye
- **Ortalama Güven Skoru:** 80.20%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Filminin Bilgileri, teknoloji devi, yapay zeka, 99 dakika, 14,573`)
```text
Soulm8te Filminin Bilgileri
Büyük bir teknoloji devi şirketini satın alır: Yas tutan mühendis; yeni
yapay zeka programını test etmekle gorevlendınılır; takat yapay zekayı
gerçek bir ruh eşi nlacak şekilde programlamaya çalıştığında;
IMDb Puani
(10021 oy) Fragman
Süre 99 dakika
izlenme 14,573 izlenme
Yıl - Ülke 2026 ABD
Türkar Gzrilim Saiznaz Fiction Korku
Kategori Filmler 108Op Film izle
'David
5 0 U L M 8 T E Rysdahl
filmleri
Lily Sull_  David R_ Claudia_Arty Fr_Elijah Is_   Mara Huf   Isabelle .
Sara / Lydia David Was.Aubrey Mac Ben Hoffma Terrance Lizzie Circe
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.76 saniye
- **Ortalama Güven Skoru:** 75.14%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Filminin Bilgileri, teknoloji devi, yapay zeka, 99 dakika, 14,573`)
```text
Soulmste Filminin Bilgileri
Büyük bir teknoloji devi şirketini satin alir.Yas tutan mühendis, yeni
yapay zeka programini test etmekle goreviendirilir.Fakat yapay zekayı,
gerçek bir ruh egi alacak sekilde programlamaya calistiginda,
beklerimedik Iswekler yenşdil ve ortalik karigit.
IMDb Puan
wy Fragman
Sire 99 dakika
İzlenme 14,573 izlenme
2026 ABD
Gerilim Seienee Fiction Korku
Filmler 1080p Film izle
>
AM
i filmleri |
Lily Sull...David R..Claudia...ArtyFr...Elijah Mara Huf
```

---

## Görsel: Açık Kaynak Metin + Eğik Belge (-4°) + MS Paint Çizik & Şekiller
- **Dosya:** `sample9_opensource_paint_skew.png` (`Pipeline: clean_paint_and_deskew`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 1.10 saniye
- **Ortalama Güven Skoru:** 73.66%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Acik Kaynak, Bilgisayarli goru, derin ogrenme, Hough donusumu, Telea inpainting`)
```text
Acik Kaynak Ansiklopedi Metni - Optik Karakter Tanima Testi
Bilgisayarli goru ve derin ogrenme yontemleri; taranmis belgelerdeki
egri satirlari ve renkli kalcm ciziklerlni temizlemek icin kullanilir .
Hough donusumu egim acisini bulurken; Telea inpainting algoritmasi
harflerin uzerindeki kirmizi vc mavi sekilleri dokuyu koruyarak siler.
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.45 saniye
- **Ortalama Güven Skoru:** 90.37%
- **Anahtar Kelime Eşleşmesi:** 5/5 (`Acik Kaynak, Bilgisayarli goru, derin ogrenme, Hough donusumu, Telea inpainting`)
```text
Acik Kaynak Ansiklopedi Metni-Optik Karakter Tanima Testi
Bilgisayarli goru ve derin ogrenme yontemleri, taranmis belgelerdeki
egri satirlari ve renkli kalem ciziklerini temizlemek icin kullanilir.
Hough donusumu egim acisini bulurken, Telea inpainting algoritmasi
harflerin uzerindeki kirmizi ve mavi sekilleri dokuyu koruyarak siler.
```

---

## Görsel: Çok Sütunlu Finansal Makine Öğrenmesi Şeması ve Kartları (Bölgesel Tarama)
- **Dosya:** `sample10_diagram_clean.png` (`Pipeline: raw`)

### Motor Çıktısı: EasyOCR (Derin Öğrenme)
- **İşlem Süresi:** 0.54 saniye
- **Ortalama Güven Skoru:** 78.10%
- **Anahtar Kelime Eşleşmesi:** 3/7 (`Finansal Veriler, Sosyal Medya, Duygu Analizi`)
```text
[1. Bölge]
Finansal
Veriler
Ita

[2. Bölge]
Haberler &
Sosyal Medya

[3. Bölge]
MAKİNE
ÖGRENMEsi

[4. Bölge]
Fiyat
Tahmnini

[5. Bölge]
Duygu
Analizi

[6. Bölge]
Ris <
Profli

[7. Bölge]
Portföy
Oplimizzsyonu

[8. Bölge]
YATIRIM
DANISMANI
```

### Motor Çıktısı: PyTesseract (Hızlı Çevrimdışı)
- **İşlem Süresi:** 0.33 saniye
- **Ortalama Güven Skoru:** 76.41%
- **Anahtar Kelime Eşleşmesi:** 5/7 (`Finansal Veriler, Sosyal Medya, Makine Öğrenmesi, Fiyat Tahmini, Duygu Analizi`)
```text
[1. Bölge]
Finansal
Veriler

[2. Bölge]
Haberler
Sosyal Medya

[3. Bölge]
MAKINE
ÖĞRENMESİ

[4. Bölge]
Fiyat
Tahmini

[5. Bölge]
Duygu
Analizi

[6. Bölge]
|

[7. Bölge]
Risk
Profil
©Ö

[8. Bölge]
Portföy
Opümizasyonu|
Bd

[9. Bölge]
YATIRIM
DANIŞMANI
```

---
