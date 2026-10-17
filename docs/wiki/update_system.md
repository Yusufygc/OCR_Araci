# Uygulama İçi Güncelleme

Paketlenmiş (exe) uygulama açılışta GitHub Releases'te yeni sürüm arar; varsa "Yeni sürüm var" penceresi çıkar. **Güncelle** denince kurulum dosyası indirilir, doğrulanır, uygulama kapanır ve kurulum sessizce üstüne yazar; uygulama kendiliğinden yeniden açılır. Yayın süreci: [[release_process]]. Kök sorun ve kararlı exe: [[exe_distribution]].

## Akış

1. **Yayın:** `vX.Y.Z` etiketi push edilince Release iş akışı `KusursuzOCR-Setup-X.Y.Z.exe` ve `.sha256` dosyalarını yükler.
2. **Denetim:** `main.py`, pencere gösterildikten sonra `window.update_controller.schedule_startup_check()` çağırır (`MainWindow.__init__` içinde değil: testler ağa çıkmasın); 3 sn sonra `UpdateController.check(manual=False)` çalışır. Yalnızca **paketlenmiş uygulamada** (`sys.frozen`), `RELEASE_REPO` doluysa, ortam değişkeni `KUSURSUZOCR_NO_UPDATE_CHECK=1` değilse ve Yardım -> "Açılışta Güncellemeyi Denetle" açıksa yapılır. Ağ yoksa sessiz geçer; **Yardım -> Güncellemeleri Denetle** her sonucu gösterir (geliştirme ortamında da çalışır).
3. **Karşılaştırma:** `update_service.release_to_update` `releases/latest` etiketini `src/version.py` sürümüyle sayısal karşılaştırır (`1.10.0 > 1.9.0`). Taslak ve ön sürüm yok sayılır; atlanan sürüm açılış denetiminde gösterilmez.
4. **İndirme:** **Güncelle** -> `DownloadWorker` (arka plan thread'i), ilerleme çubuğu. Doğrulama **zorunlu**: adres, dosya adı, boyut, SHA-256 (aşağıda).
5. **Kurulum:** `Setup.exe /SILENT /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS /LOG=%TEMP%\KusursuzOCRUpdate\install.log` bağımsız süreç olarak başlatılır (kabuk yok, `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`), `quit_requested` ile ana pencere kapanır, Inno kurar, `[Run]` uygulamayı yeniden açar.

### Windows başlatmayı engellerse (SAC)

`launch_installer` önce `CreateProcess`; `WinError 4551/1260` gelirse Gezgin'in yolu (`ShellExecuteW`); ikisi de engelliyse `InstallerBlockedError`. `UpdateController` bu durumda **15 sn aralıkla en çok 40 kez** yeniden dener (pencerede "Windows bekleniyor... (n/40)", **Beklemeyi Bırak** düğmesi). Süre dolarsa ya da kullanıcı vazgeçerse dosya Gezgin'de seçili gösterilir ve **Sürüm Sayfası** düğmesi çıkar (elle kurulum). Kararlı exe ([[exe_distribution]]) sonrası bu yola girilmesi beklenmez; kurulum dosyası her sürümde yeni olduğu için tutulur.

## Katmanlar

| Katman | Dosya |
|---|---|
| Çekirdek (UI'dan bağımsız, ağ sahte `opener` ile test edilir) | `src/utils/updater/update_service.py` |
| Tercihler (`~/.kusursuzocr/updates.json`: açılış denetimi, atlanan sürüm) | `src/utils/updater/update_prefs.py` |
| Arka plan işleri | `src/ui/workers/update_workers.py` (`UpdateCheckWorker`, `DownloadWorker`) |
| Akış yönetimi, menü, yeniden deneme | `src/ui/update_controller.py` (`UpdateController`) |
| Görünüm | `src/ui/components/update_dialog.py` (`UpdateDialog`) |
| Metinler | `UIStrings` (`UPDATE_*`, `BTN_UPDATE_*`, `MENU_HELP`) |

## Güvenlik

- Depo adı `sahip/depo` biçiminde olmalı; `.` ve `..` parçaları reddedilir.
- İndirme adresi yalnızca `https://github.com/<depo>/releases/download/...`; yönlendirme yalnızca `github.com` / `*.githubusercontent.com` (yönlendirme işleyicisi + son adres denetimi).
- Dosya adı sıkı desene uymalı: `KusursuzOCR-Setup-X.Y.Z.exe` (sürüm, etiketle aynı olmalı).
- Boyut: Release'teki boyutla birebir eşleşir ve en çok 2 GiB (GitHub sınırı; torch/EasyOCR nedeniyle 400 MB yetmez).
- **SHA-256 zorunlu:** GitHub asset `digest` alanından, yoksa `<dosya>.sha256` dosyasından; ikisi de yoksa güncelleme **reddedilir**. Uyuşmazlıkta dosya silinir.
- Kimlik bilgisi gönderilmez; yanıt boyutu ve süre sınırlıdır; sürüm notu düz metin gösterilir; sayfa düğmesi yalnızca izinli host'lara açılır.
- **Sınır (kabul edildi):** özet GitHub'dan gelir; hesap ele geçirilirse sahte dosya + sahte özet yayınlanabilir (imza yok, imzalama yapılmıyor).

## Sınırlar ve doğrulama durumu

- Yalnızca Windows. İndirme sürerken iptal düğmesi yoktur.
- `RELEASE_REPO` = `Yusufygc/OCR_Araci`. Henüz Release yayınlanmadığı için denetim yalnızca yeni etiket çıkınca anlamlı sonuç verir.
- **Doğrulanan:** `tests/test_update_service.py`, `tests/test_update_controller.py`, `tests/test_update_prefs.py` (sahte ağ/servis ile). **Doğrulanmayan:** gerçek bir Release üzerinden uçtan uca güncelleme ve SAC'lı makinede kurulum; iki sürüm yayınlandıktan sonra [[release_process]] kontrol listesiyle denenmelidir.
