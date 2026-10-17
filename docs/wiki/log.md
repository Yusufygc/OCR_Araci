# Kronolojik Değişiklik Günlüğü (Wiki Log)

Bu dosya, projedeki mimari kararların, kaynak içeri alımlarının (ingest), kod inceleme ve refactoring işlemlerinin kronolojik kayıt defteridir. Yeni kayıtlar dosyanın **en üstüne** eklenir.

---

## [2026-10-17] [FIX] | Ad Değişikliği (OCR Aracı), Donmuş Exe torchvision Hatası, CI Hataları ve Tanıtım README'si
- **Ad:** "Kusursuz" kaldırıldı. Uygulama adı `OCR Aracı`, exe `OCRAraci.exe`, kurulum dosyası `OCRAraci-Setup-X.Y.Z.exe`, Inno betiği `packaging/OCRAraci.iss`, tercih klasörü `~/.ocraraci`, ortam değişkenleri `OCRARACI_NO_UPDATE_CHECK` / `OCRARACI_SELFTEST_OUT`. Kod, testler ve wiki buna göre güncellendi. Inno betiğine UTF-8 BOM eklendi (BOM'suz betik ANSI sayılır, Türkçe metinler bozulur).
- **Donmuş exe hatası** (`operator torchvision::nms does not exist`, uygulama açılışta çöküyordu): torchvision'ın `_C_stable.pyd` ve `image_stable.pyd` uzantı modüllerini PyInstaller toplamıyordu (`--collect-binaries` yalnız DLL toplar). `build_exe.torchvision_extension_arguments()` her `.pyd`/`.so` için `--add-binary` ekler. Önceki "8 sn açık kaldı" denemesi bu hatayı yakalayamadı: hata penceresi de süreci açık tutar.
- **Yeni kapı `--selftest`:** `src/selftest.py`, `OCRAraci.exe --selftest` başsız olarak torchvision `nms`, EasyOCR motoru, OpenCV hattı ve dışa aktarıcıları çalıştırır. `build_installer.py` bunu CI dahil her zaman derlenen exe'ye, yerelde ayrıca deneme kurulumundaki exe'ye uygular; başarısızsa yayın durur. Kapı eksik binary'li exe'yi gerçekten yakaladı ve düzeltmeden sonra geçti.
- **CI (`test.yml`, ubuntu):** `libEGL.so.1` yoktu, bu yüzden PySide6 içe aktarılamadı (5 test modülü hata verdi, PDF dışa aktarma testleri düştü). `apt-get install` adımı eklendi (Qt kütüphaneleri, `fonts-dejavu-core`, `tesseract-ocr` + `tur`/`eng`). Testlerdeki `ResourceWarning`'ler giderildi. **Bu düzeltme Linux'ta henüz çalıştırılamadı;** ilk push'ta Actions sonucuna bakılmalı.
- **README:** ajan görev listesi yerine tanıtım belgesi (özellikler, kurulum, kaynaktan çalıştırma, mimari, belgeler, bilinen sınırlar).
- **Doğrulama (bu makine, 2026-10-17):** yeni kararlı exe özeti `40627b420d2c5b0557e69a3211c70d1ec41f78451289fc5651bdcba67f0bceb4` (ad ve ikon değişti, bilerek yeni özet; önceki `8a26fc2f…` geçersiz). `build_installer.py` tam akışı: selftest BASARILI, exe açıldı, `OCRAraci-Setup-1.0.0.exe` (176 MB) derlendi (171 sn), geçici dizine kurulup selftest + açılış + kaldırıcı denendi, kayıt/kısayol iz bırakmadı. Testler 138+, `verify.py` sıfır yeni bulgu.
- **Doğrulanmadı:** Linux CI düzeltmesi, CI'da (`windows-latest`) derlenen exe özetinin yerelle aynı olduğu, SAC'lı başka makinede kurulum, gerçek Release üzerinden güncelleme, donmuş exe içinde gerçek bir görselde OCR (selftest motoru yükler ama model indirmez).

## [2026-10-17] [DEPLOY] | Güncelleme Deposu Ayarlandı ve Kod GitHub'a Gönderildi
- Depo `https://github.com/Yusufygc/OCR_Araci` (public) olarak bağlandı; yerel dal `main` olarak yeniden adlandırılıp `origin/main`'e gönderildi (eski yerel `master` dalı durur).
- `src/version.py`: `RELEASE_REPO = "Yusufygc/OCR_Araci"`; uygulama içi güncelleme denetimi artık yapılandırılmış depoya bakar (yalnızca paketlenmiş exe'de açılışta, [[update_system]]).
- Henüz etiket/Release yok: ilk `python tools/release.py X.Y.Z` + `git push origin vX.Y.Z` kullanıcı isteğiyle yapılır ([[release_process]]). CI'da derlenen exe özetinin yerelle aynı olduğu ilk Release'te doğrulanacak.

## [2026-10-17] [DEPLOY] | Kararlı exe, Inno Kurulum, Sürüm/Yayın Süreci, Uygulama İçi Güncelleme ve Uygulama İkonu
Üç kılavuza (exe dağıtımı, güncelleme sistemi, sürüm yayınlama) göre sistem uyarlandı. Kullanıcı kararları: **kod imzalama ve lisanslama yapılmaz** (Inno betiğinde `LicenseFile`/imza yok, `LICENSE` eklenmedi).
- **Paketleme:** `ocr_app.spec` kaldırıldı; `build_exe.py` (PyInstaller 6.22.3, `--onedir --noupx --debug=noarchive`, sabit `SOURCE_DATE_EPOCH`), `packaging/launcher.py` (sabit giriş), `launcher_version_info.txt`, onay kapısı `packaging/launcher.sha256`, `build_installer.py`, `build_verify.py`, `packaging/OCRAraci.iss` (sabit `AppId`, `PrivilegesRequired=lowest`, `RelaunchAfterUpdate`), `.gitattributes` (`eol=lf`), `requirements-build.txt`. Bkz. [[exe_distribution]], [[deployment]].
- **Sürüm/yayın:** `src/version.py` tek kaynak, `tools/release.py` (commit + ek açıklamalı etiket, itmez; `main` ya da `master`), `.github/workflows/release.yml` (etiket denetimi, test, `build_installer.py`, `gh release create --verify-tag`). Bkz. [[release_process]].
- **Güncelleme:** `src/utils/updater/` (`update_service`, `update_prefs`), `UpdateController`, `UpdateDialog`, `update_workers`, Yardım menüsü. Güvenlik: yalnız `github.com` adresleri, sıkı dosya adı, boyut (en çok 2 GiB), **zorunlu SHA-256**, depo adında `.`/`..` reddi (testle yakalanan açık). Bkz. [[update_system]].
- **İkon:** `tools/make_icon.py` ile `packaging/app_icon.ico` (16-256 px) ve `src/ui/assets/app_icon.png`; exe, kurulum sihirbazı, kısayol, pencere ve görev çubuğunda kullanılır ([[ui_system]]).
- **Doğrulama (bu makine, Windows 11, 2026-10-17):** kararlı exe özeti `8a26fc2f422ac7ddb0f698072b04e6676c9807e5f0381a5286175ebd3cea952c`. Kaynak koduna satır eklenip yeniden derlendi: kapı "onaylananla aynı" dedi (1 ek deneme). `build_installer.py` tam akışı 1 denemede geçti: exe 8 sn açık kaldı, `OCRAraci-Setup-1.0.0.exe` (175 MB) derlendi (163 sn), geçici dizine sessiz kuruldu, açıldı, kaldırıcı çalıştı; kayıt defteri ve kısayol iz bırakmadı. Exe ve kurulum dosyasında gömülü ikon var (`ExtractIconEx`). Testler 131/131, `verify.py` sıfır yeni bulgu.
- **Doğrulanmadı:** CI'da (`windows-latest`) derlenen exe özetinin yerel özetle aynı olduğu; indirilmiş (MOTW'li) kurulum dosyasının SAC'lı başka makinede açıldığı; gerçek Release üzerinden uygulama içi güncelleme; donmuş exe içinde gerçek OCR çalıştırma (yalnız açılış denendi). `RELEASE_REPO` boş (depo GitHub'a gönderilmedi), bu yüzden güncelleme denetimi kapalı.

## [2026-10-17] [FIX] | Gerçek Kullanıcı Testinde Bulunan 4 Hata Giderildi
- **Overlay çökmesi:** `CanvasOverlayManager.clear()` silinmiş C++ öğelerinde `RuntimeError` fırlatıyordu; OCR sonrası ikinci OCR başlamıyor, yeni görsel "Görsel okunamadı" hatası veriyordu. `scene()` kontrolü ve `RuntimeError` yakalama eklendi.
- **Deskew polarite:** `_estimate_skew_angle` koyu temalı görselde zemini satır sanıp -14°/-17° yanlış eğim uyguluyor ve Tesseract 0 karakter okuyordu (sample1/6: 0/5 -> 5/5). Metin maskesi polariteye göre çıkarılıyor; `deskew` kenar dolgusu arka plan renginden alınıyor. Aynı sınıf hata `remove_color_annotations` kalın çekirdek dolgusunda da (koyu zeminde beyaz leke) giderildi.
- **Kutu koordinatları:** 2x büyütme, 16px pad ve ROI ofseti kutulara yansıtılmıyordu (kutular görsel dışına taşıyordu). `prepare_for_ocr_with_transform`, `restore_details_coordinates`, `shift_details_coordinates` ve `ImageCanvas.get_primary_region_offset` eklendi.
- **multi_region:** Worker'a ilk bölgenin kırpımı veriliyordu, ikinci bölge kırpımın dışında kalıp kayboluyordu. Bu modda tam görsel verilir (`ImageCanvas.get_full_cv_image`).
- Yeni testler: `tests/test_main_window_ocr_flow.py`, `tests/test_image_processor_polarity.py`, `test_ocr_engines.py` ve `test_overlay_manager.py` eklemeleri (67/67 başarılı, `verify.py` sıfır yeni bulgu).
- Bilinen kalan risk (kod değişmedi): Varsayılan açık `CLAHE` filtresi Tesseract'ta şema görsellerinde metni siliyor (sample10: yalnız `contrast` -> 0 bölge); `binarize_adaptive` koyu/fotoğraflı arayüzlerde metni bozuyor.

## [2026-10-17] [FIX] | "Word Kaydet" Buton Metni Düzeltildi ve Dosya Kaydında Bölge Başlıkları Temizlendi
- `UIStrings`: "Word (DOCX) Olarak Kaydet" metni sağ panel buton genişliğine sığmayıp "Word (DOCX) Olarak Kay" şeklinde kesiliyordu. Buton metinleri sadeleştirilerek `Word Kaydet`, `TXT Kaydet` ve `PDF Kaydet` olarak güncellendi.
- `TextEditorPanel.strip_region_headers`: Dosyaya dışa aktarırken (`export_document`) `[1. Bölge]`, `[2. Seçili Bölge]` gibi dahili bölge etiketleri düzenli ifadeyle temizlenerek Word (.docx), TXT ve PDF dosyalarının temiz paragraf metinleri olarak kaydedilmesi sağlandı.
- `TextEditorPanel.init_ui`: Fonksiyon metrikleri kuralı (maks 35 satır) gereği buton oluşturma mantığı `_build_action_buttons` yardımcı metoduna ayrıştırıldı.
- `tests/test_ui_components.py`: `test_text_editor_strip_region_headers` birim testi eklendi (56/56 test başarılı, `verify.py` sıfır bulgu).

## [2026-10-17] [FEAT] | Bölgesel ve Blok Tabanlı Tarama, Tak-Çıkar Strateji Deseni ve Tıklanabilir Kutu Katmanı Eklendi
- `src/core/layout/`: `ILayoutAnalyzer` ve `XYCutLayoutAnalyzer` 2D uzamsal boşluk analizi ve hiyerarşik okuma sırası düzenleyicisi kuruldu. Akış şemaları ve çok sütunlu infografiklerde paralel blokların yatayda birbirine karışması (`Fiyat Duygu Risk Portföy / Tahmini Analizi Profili Optimizasyonu`) çözüldü; her blok `[1. Bölge: Finansal Veriler]`, `[4. Bölge: Fiyat Tahmini]`, `[5. Bölge: Duygu Analizi]` şeklinde yapısal olarak ayrıştırıldı.
- `src/core/strategies/`: `IScanStrategy` sözleşmesi ve `ScanStrategyFactory` tak-çıkar fabrika mimarisi kuruldu. Kod bağımlılığı olmadan modlar eklenebilir: `LineScanStrategy` (Düz metin / satır satır), `BlockScanStrategy` (Bölgesel / şema blokları) ve `MultiRegionStrategy` (Seçili alanlar).
- `src/ui/components/overlay_manager.py`: `CanvasOverlayManager` ve `ClickableBoxItem`. `ImageCanvas` mantığından bağımsız çalışan katman; tespit edilen metin kutularını yarı şeffaf yeşil çerçevelerle çizer, fare üzerine gelince hover vurgusu yapar ve tıklandığında metni işletim sistemi panosuna kopyalar.
- `src/ui/components/image_canvas.py`: Çoklu seçim desteği (`_crop_items`), Shift + Sol tık ile çoklu ROI ekleme, sağ tık ile temizleme ve overlay kutularına tıklama önceliği sağlandı.
- `src/ui/main_window.py`: Üst çubuğa `cmb_scan_mode` (Tarama modu seçici) ve alt kontrol alanına `chk_overlay` ("Metin Kutularını Göster" aç/kapa) eklendi.
- Birim Testler ve Doğrulama: `test_layout_analyzer.py`, `test_scan_strategies.py` ve `test_overlay_manager.py` eklenerek test sayısı 55'e çıkarıldı (55/55 başarılı). `verify.py` sıfır yeni bulgu ile doğrulandı. `REAL_TEST` 10 senaryo x 2 motor = 20 OCR koşumuna genişletildi (`REPORT.md` güncellendi).

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
