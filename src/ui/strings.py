"""
Merkezi Kullanıcı Arayüzü Metinleri (Localization & UI Strings).
Uygulama genelinde hardcoded metin ve emoji kullanımını engelleyen tek doğruluk kaynağı (Single Source of Truth).
"""


class UIStrings:
    # Uygulama Başlığı ve Durum Çubuğu
    APP_TITLE = "Kusursuz OCR - Yerel Metin Ayrıştırma"
    STATUS_BAR_READY = "Kusursuz OCR Uygulaması | Hazır"

    # Üst Kontrol Çubuğu
    BTN_OPEN_IMAGE = "Görsel Yükle"
    LBL_ENGINE = "OCR Motoru:"
    LBL_LANGUAGE = "Dil:"
    LANG_TUR_ENG = "Türkçe + İngilizce"
    LANG_TUR = "Türkçe"
    LANG_ENG = "İngilizce"

    # Durum Bildirimleri
    STATUS_READY = "Hazır. Bir görsel yükleyin..."
    STATUS_LOADED = "Yüklendi: {filename}"
    STATUS_DRAG_DROPPED = "Görsel tuvale aktarıldı."
    STATUS_PROCESSING = "Metinler ayrıştırılıyor... Lütfen bekleyin."
    STATUS_SUCCESS = "Tamamlandı! Süre: {time:.2f} sn | Doğruluk Oranı: %{confidence:.1f}"
    STATUS_ERROR = "İşlem sırasında hata oluştu."
    STATUS_FAILED = "İşlem başarısız."
    STATUS_BAR_SUCCESS = "OCR Başarılı - {time:.2f} saniye sürdü."

    # OCR Butonu
    BTN_RUN_OCR = "Metni Ayrıştır"

    # Filtre Paneli
    GROUP_FILTERS = "Görüntü İyileştirme ve Temizleme Filtreleri"
    CHK_GRAYSCALE = "Gri Tonlama (Grayscale)"
    CHK_CONTRAST = "Kontrast Artırma (CLAHE)"
    CHK_DENOISE = "Gürültü Temizleme (Denoise)"
    CHK_THRESHOLD = "Keskin Siyah-Beyaz (Binarization)"
    CHK_REMOVE_COLOR = "Renkli Çizim ve Notları Temizle (Color Mask)"
    CHK_DESKEW = "Açı Düzeltme (Deskew)"
    BTN_RESET_FILTERS = "Filtreleri Sıfırla"

    # Metin Editörü Paneli
    GROUP_OUTPUT = "Ayrıştırılan Metin ve Çıktı"
    EDITOR_PLACEHOLDER = "Görsel yükleyip 'Metni Ayrıştır' butonuna bastığınızda ayrıştırılan metin burada görüntülenecektir..."
    STATS_FORMAT = "Kelime: {words} | Karakter: {chars} | Satır: {lines}"
    BTN_COPY_TEXT = "Metni Kopyala"
    BTN_EXPORT_TXT = "TXT Olarak Kaydet"
    BTN_EXPORT_DOCX = "Word (DOCX) Olarak Kaydet"
    BTN_EXPORT_PDF = "PDF Olarak Kaydet"

    # Diyaloglar ve Mesajlar
    DIALOG_OPEN_IMAGE = "Görsel Seç"
    FILTER_IMAGE_FILES = "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)"
    DIALOG_SAVE_TITLE = "Metni Kaydet ({format_name})"
    MSG_COPIED_TITLE = "Kopyalandı"
    MSG_COPIED_BODY = "Metin panoya başarıyla kopyalandı."
    MSG_NO_TEXT_TITLE = "Uyarı"
    MSG_NO_TEXT_BODY = "Dışa aktarılacak veya kopyalanacak metin bulunmuyor."
    MSG_NO_IMAGE_BODY = "Lütfen önce bir görsel yükleyin."
    MSG_SAVE_SUCCESS = "Dosya başarıyla kaydedildi:\n{path}"
    MSG_SAVE_ERROR = "Dosya kaydedilirken bir hata oluştu."
    MSG_ENGINE_NOT_AVAILABLE = "Seçilen motor ({engine_name}) sisteminizde hazır değil."
    MSG_ENGINE_CREATE_ERROR = "Motor oluşturma hatası: {error}"
    MSG_UNEXPECTED_ERROR = "Beklenmeyen İşlem Hatası: {error}"
