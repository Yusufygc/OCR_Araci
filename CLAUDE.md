# CLAUDE.md — P021-OCR AI Çalışma Giriş Kapısı

Bu proje bir **LLM Wiki** sistemiyle (`docs/wiki/`) yönetilmektedir.

## ⚠️ Zorunlu Talimat (No Zero-Context)
Kod yazmadan, mimari karar vermeden veya bir göreve başlamadan önce **MUTLAKA** `docs/wiki/index.md` dosyasını oku. Gerekli konseptler için çift köşeli parantezli `[[sayfa_adi]]` bağlantılarını takip et. Projeyi sıfırdan keşfetme; var olan mimari kararları kullan.

## 📋 Operasyon Komutları
- **[INGEST]**: Yeni bir kaynak/belge geldiğinde analiz et, `docs/wiki/` altında ilgili sayfayı oluştur/güncelle, `index.md` ve `log.md`'ye kaydet.
- **[QUERY]**: Projeyle ilgili sorularda önce `docs/wiki/` sayfalarını sentezle; kalıcı bir kararsa wiki'ye yeni sayfa ekle.
- **[LINT]**: `docs/wiki/` klasörünü tara, çelişkili bilgi, öksüz sayfa ve kırık link kontrolü yapıp raporla.

## 🔗 Referanslar
- **Wiki Anayasası:** `docs/wiki/rules.md`
- **İçerik Haritası:** `docs/wiki/index.md`
- **Kronolojik Günlük:** `docs/wiki/log.md`
