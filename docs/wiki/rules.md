# Proje ve LLM Wiki Anayasası

Bu doküman, bu projede AI ile çalışırken kullanılan wiki mekanizmasını, operasyonel iş akışını, kod inceleme ve kalite kurallarını tanımlar. `docs/wiki/` klasöründeki bilgi tabanının temel anayasasıdır.

## 1. Sistem Mimarisi (3 Katman)

1. **Raw Sources (Ham Kaynaklar):** Dışarıdan gelen dokümanlar, veri setleri, spesifikasyonlar. Sabittir (immutable), sadece okunur.
2. **The Wiki (`docs/wiki/`):** AI'ın tam kontrole sahip olduğu, Obsidian stili çift köşeli bağlantılarla (`[[sayfa_adi]]`) birbirine bağlı Markdown dosyalarıdır.
3. **The Schema (Bu Dosya):** Çalışma kurallarını belirleyen anayasadır.

## 2. Temel Kurallar (Zorunlu Çalışma Akışı)

- **Önce Oku (No Zero-Context):** Kod yazmadan, mimari karar vermeden önce MUTLAKA [[index]] dosyasını oku. İhtiyaç duyulan konseptlerde alt sayfalara git. Projeyi sıfırdan keşfetme.
- **Proaktif Güncelleme (Bookkeeping):** Yeni kütüphane, mimari değişiklik, algoritma veya yapılandırma yapıldığında aynı turda ilgili wiki sayfasını güncelle veya yenisini oluştur. [[log]] ve [[index]] dosyalarını güncelle.
- **Bağlantısallık:** Her sayfada diğer ilgili sayfalara `[[link]]` ver. Öksüz sayfa ve kırık link bırakma. Doküman içinde örnek gösterirken çift köşeli parantezi kod bloğu içine al: `` `[[ornek]]` ``.

## 3. Kritik Navigasyon Dosyaları

- **[[index]]:** Tüm wiki'nin içerik haritasıdır. Kategorilere ayrılmış sayfa listesi ve tek cümlelik özetleri içerir.
- **[[log]]:** Kronolojik kayıt defteridir. Her önemli işlem dosyanın en üstüne şu formatta eklenir:
  `## [YYYY-AA-GG] [İŞLEM_TİPİ] | Kısa Açıklama`
  (İşlem Tipleri: `INGEST`, `REVIEW`, `REFACTOR`, `LINT`, `DEPLOY`)

## 4. Operasyon Komutları

| Komut | Eylem |
|---|---|
| **[INGEST]** | Kaynağı oku/analiz et → `docs/wiki/` içinde yeni sayfa aç → çelişenleri güncelle → [[index]]'e ekle → [[log]]'a kaydet |
| **[QUERY]** | Önce [[index]] ve ilgili sayfaları oku → sentezlenmiş yanıt üret → kalıcı mimari kararları wiki'ye işle |
| **[LINT]** | Tüm `docs/wiki/` klasörünü tara → çelişki, öksüz sayfa, kırık link tespit et → raporla ve onayla düzelt |

## 5. Kodlama ve Commit Standartları

- **Dil & Karakter:** Kod ve commit mesajları Türkçe; Türkçe glifler (ı, ğ, ü, ş, ö, ç, İ, Ğ, Ü, Ş, Ö, Ç) korunur.
- **Yapay Zeka İzleri:** Commit ve PR mesajlarında AI referansı (🤖, "Co-Authored-By", "Generated with") yer almaz.
- **Doğrulama:** Değişiklikler her adımda `python -m unittest discover tests` ve `python verify.py` ile doğrulanır.
