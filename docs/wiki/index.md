# Proje Bilgi Tabanı İçerik Haritası (Wiki Index)

Bu sayfa, P021-OCR projesinin tüm mimari, tasarım, veri işleme ve dağıtım kararlarının merkezi navigasyon haritasıdır.

---

## 📌 Anayasa ve Kurallar
- [[rules]] — AI destekli geliştirme kuralları, operasyon komutları ve commit disiplini.
- [[log]] — Yapılan tüm mimari, kod ve bakım işlemlerinin kronolojik kayıt defteri.

---

## 🏛️ Mimari ve Tasarım
- [[architecture]] — Katmanlı mimari yapısı, Strategy/Factory desenleri ve Qt asenkron sinyal akışı.
- [[ocr_engines]] — EasyOCR ve Tesseract motorlarının çalışma ilkeleri, dil eşleme ve fabrika mimarisi.
- [[image_processing]] — OpenCV tabanlı önişleme boru hattı (CLAHE, Denoise, Color Mask, Deskew, Binarize).
- [[exporters]] — Ayrıştırılan metinlerin TXT, Word (.docx) ve PDF formatlarında dışa aktarılma mekanizması.
- [[ui_system]] — Merkezi arayüz metinleri (UIStrings) ve platform-native ikon sağlayıcısı (IconProvider).

---

## 🚀 Dağıtım ve Altyapı
- [[deployment]] — Paketleme özeti (PyInstaller + Inno Setup), derleme komutu ve GitHub Actions iş akışları (`test.yml`, `release.yml`).
- [[exe_distribution]] — Kararlı exe tasarımı, Akıllı Uygulama Denetimi (SAC) gerekçesi, özet kapısı, Inno betiği, derleme/doğrulama betikleri.
- [[release_process]] — Sürüm numarası, `tools/release.py`, etiketle GitHub Release yayını, kontrol listesi ve geri alma.
- [[update_system]] — Uygulama içi güncelleme: denetim, doğrulamalı indirme, sessiz kurulum, SAC için yeniden deneme.
