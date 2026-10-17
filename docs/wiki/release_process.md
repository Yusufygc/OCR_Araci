# Sürüm Yayınlama Süreci

Yeni sürüm **etiket** ile yayınlanır: `vX.Y.Z` etiketi push edilince GitHub Actions testleri koşar, kararlı exe ile Inno kurulum dosyasını derler ve GitHub Releases'e yükler. Kurulu uygulamalar açılışta bu yayını görüp güncelleme teklif eder ([[update_system]]). Arka plan: [[exe_distribution]].

## Sürüm numarası

- Biçim `MAJOR.MINOR.PATCH` (`1.0.0`); etiket `v` önekli (`v1.0.0`). `-rc1` gibi ön sürümler güncelleyici tarafından yok sayılır.
- **Tek kaynak:** `src/version.py` (`__version__`, `RELEASE_REPO`). Kurulum dosyası sürümü bundan alır (`/DAppVersion`). exe'nin Windows sürüm kaynağı **bilerek yükseltilmez** ([[exe_distribution]]).
- Artış: hata düzeltme -> PATCH, özellik -> MINOR, geriye dönük uyumsuz değişiklik -> MAJOR.

## Güncelleme deposu

`src/version.py` içindeki `RELEASE_REPO` `Yusufygc/OCR_Araci` olarak ayarlıdır (uzak depo: `origin`, varsayılan dal `main`). Depo adı değişirse bu değer de güncellenmelidir; boş bırakılırsa uygulama içi güncelleme denetimi kapanır. Henüz hiçbir Release yayınlanmadığı için `releases/latest` yanıtı yoktur; ilk `vX.Y.Z` etiketi yayınlanana kadar denetim "güncel" ya da hata sonucu verir.

## Yayın adımları

Ön koşul: testler yeşil, çalışma ağacı temiz, dal `main` (ya da `master`).

```powershell
python tools/release.py 1.0.1         # src/version.py günceller, "chore(release): v1.0.1" commit'i ve ek açıklamalı v1.0.1 etiketini oluşturur (itmez)
git push origin main
git push origin v1.0.1                # --follow-tags KULLANMA: hafif etiketleri göndermez
gh run watch                          # Release iş akışını izle
gh release view v1.0.1                # kurulum dosyası ve .sha256 oluştu mu
```

`.github/workflows/release.yml` (`windows-latest`, Python 3.10) sırayla:

1. Etiket ile `src/version.py` aynı değilse **durur** (`tools/release.py --check-tag`; etiket adı `env: TAG` ile verilir, betiğe gömülmez).
2. Bağımlılıkları kurar (`requirements.txt`, `requirements-build.txt`), `python -m unittest discover tests` koşar; kırmızıysa yayın yok.
3. Inno Setup yoksa `choco install innosetup -y`.
4. `python build_installer.py`: kararlı exe derlenir, **`--selftest` ile çalışma zamanı bağımlılıkları sınanır (başarısızsa yayın durur)**, **özet `packaging/launcher.sha256` ile karşılaştırılır (farklıysa yayın durur)**, `OCRAraci-Setup-X.Y.Z.exe` ve `.sha256` üretilir (CI'da SAC denemesi atlanır).
5. `gh release create ... --generate-notes --verify-tag` (`-` içeren etiket ön sürüm olur).

## Kontrol listesi

- [ ] Testler ve `python verify.py` temiz; davranış değiştiyse wiki güncel.
- [ ] `python tools/release.py X.Y.Z` çalıştırıldı; etiket `v` + `__version__` ile aynı.
- [ ] Release iş akışı yeşil; günlükte "Kararlı exe özeti onaylananla aynı".
- [ ] Release'te `OCRAraci-Setup-X.Y.Z.exe` ve `.sha256` var.
- [ ] **İndirilmiş (MOTW'li) kurulum dosyasını SAC'lı gerçek bir makinede aç** (CI'da SAC yoktur; CI'ın dosyası hiç denenmemiş dosyadır). Yayına yüklediğin dosya denediğin dosya olmalı: yeniden paketleme özeti değiştirir.
- [ ] Önceki sürümden uygulama içi güncellemeyi dene: pencere çıktı mı, kurulum başladı mı, uygulama yeniden açıldı mı, Yardım menüsünde yeni sürüm görünüyor mu.

## Hata ve geri alma

| Durum | Ne yapılır |
|---|---|
| Etiket ile `__version__` farklı, iş akışı durdu (yayın yok) | Düzelt, commit'le, etiketi taşı: `git tag -f vX.Y.Z`, `git push -f origin vX.Y.Z` |
| Yayın oluştu ama sürüm hatalı | **Yayınlanmış etiketi taşıma.** Yeni PATCH çıkar. Acilse `gh release delete vX.Y.Z --cleanup-tag` |
| Kapı "özet DEĞİŞTİ" dedi | [[exe_distribution]] bölüm "Exe'yi bilerek değiştirmek" |
| `git push` etiketi göndermedi | `git push origin vX.Y.Z` ayrıca |
| Kurulu kullanıcıda güncelleme başlamadı | `%TEMP%\OCRAraciUpdate\install.log` |

## Güvenlik ve sınırlar

- Yayın, tüm kurulu kullanıcılara güncelleme penceresi çıkarır. **Yapay zeka asistanları kullanıcının açık isteği olmadan etiket oluşturmaz, etiket push etmez.**
- Kurulum dosyası **imzasızdır** (karar: imzalama ve lisanslama yapılmaz); SmartScreen uyarısı ve SAC engeli olabilir. Kullanıcı notu: SmartScreen'de "Ek bilgi -> Yine de çalıştır"; SAC engelinde bu seçenek yoktur, "birkaç dakika sonra aynı dosyayı yeniden çalıştır / yeni sürümü indir".
- Release dosya boyutu sınırı 2 GiB'dır; torch/EasyOCR içeren kurulum dosyası büyüktür, sınıra yaklaşırsa sıkıştırma/içerik gözden geçirilmelidir.
- Yalnızca Windows.
