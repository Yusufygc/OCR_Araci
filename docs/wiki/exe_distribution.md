# Windows exe Dağıtımı: Kararlı exe, Kurulum Sihirbazı ve Akıllı Uygulama Denetimi

Bu sayfa, imzasız Kusursuz OCR uygulamasının sorunsuz kurulması için kullanılan **kararlı exe** tasarımını ve gerekçesini toplar. Sürüm / yayın adımları: [[release_process]]. Uygulama içi güncelleme: [[update_system]]. Eski paketleme notları ve CI: [[deployment]].

**Karar (kullanıcı):** kod imzalama ve lisanslama yapılmaz. İmza sertifikası, SignPath benzeri hesap/başvuru, `LICENSE` / bildirim dosyası bu çalışmanın kapsamı dışındadır; Inno betiğinde `LicenseFile` ve imza yönergeleri bilinçli olarak yoktur (`tests/test_release_packaging.py` bunu denetler).

---

## 1. Kök sorun: Akıllı Uygulama Denetimi (SAC)

Windows 11'de SAC açıksa imzasız her çalıştırılabilir dosya (exe, DLL, kurulum dosyası, kaldırıcı) dosya özetine (SHA-256) göre Microsoft bulut itibar kararına bırakılır.

- Karar **dosya başına ve öngörülemezdir**: aynı kaynaktan iki derlemenin özeti farklıdır, biri çalışır diğeri engellenir. Konuma, yetkiye, `onefile`/`onedir` ayrımına, indirme işaretine (MOTW) bağlı olmadığı gözlenmiştir; içeriğe bağlıdır.
- Kullanıcı başına izin listesi yoktur. **SAC'ı kapatmak ya da güvenlik ayarlarına dokunmak çözüm değildir ve önerilmez.**
- Belirtiler: "Uygulama Denetimi ilkesi bu dosyayı engelledi", Python `OSError: [WinError 4551]`, bash `Permission denied` (126).
- Kanıt: `Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational"` içinde olay `3077` / `3033`.

Güncelleme zincirinde asıl zarar: her sürümde yeni exe özeti, kurulan **yeni exe**'nin engellenmesi demektir. Çözüm: exe'yi sürümler arasında **değiştirmemek**.

> Ölçümler başka bir projeden (GitClean Archiver, 2026-10-11/12) alınmış kılavuz bilgisidir; bu depoda yeniden ölçülmedi. Windows sürümü değişince yeniden doğrula.

## 2. Kararlı exe: her sürümde bayt bayt aynı exe

SAC yalnızca yeni çalıştırılabilir dosyayı değerlendirir. Uygulama kodu exe'nin dışında durursa bir kez onaylanan exe sonraki tüm sürümlerde aynı kalır; güncellemeyle yalnızca `.pyc` ve veri dosyaları değişir. Dört parçanın hepsi gerekli:

| Parça | Uygulama | Neden |
|---|---|---|
| Sabit giriş betiği | `packaging/launcher.py` yalnızca `src.main.main()` çağırır. **Asla değiştirilmez** | İçeriği exe'ye gömülür |
| Modüller exe dışında | `--debug=noarchive` (`_internal` altında `.pyc`) | Sürümle değişen kod exe'yi değiştirmesin |
| Sabit zaman damgası | `os.environ["SOURCE_DATE_EPOCH"] = str(LAUNCHER_EPOCH)` (`build_exe.py`) | Yalnız `noarchive` yetmez, PE zaman damgası özeti değiştirir |
| Sabit sürüm kaynağı | `packaging/launcher_version_info.txt` (`1.0.0.0`) | Sürümle değişen kaynak exe'yi değiştirir |
| Sabit ikon | `packaging/app_icon.ico` (`--icon`) | İkon exe'ye gömülür; değişirse özet değişir. Dosyanın SHA-256 değeri testte sabittir |

Bedel: Gezgin'de exe → Özellikler hep `1.0.0.0` gösterir; ürün sürümü `src/version.py`, kurulum dosyası, "Uygulamalar ve özellikler" kaydı ve Yardım menüsünde görünür.

Özet; PyInstaller sürümü (`requirements-build.txt`, `pyinstaller==6.22.3` sabit), Python sürümü (CI ve yerel 3.10), ad, sürüm kaynağı, giriş betiği ve epoch'tan oluşur. Satır sonları `.gitattributes` ile LF'ye sabitlenmiştir. `--noupx` zorunludur (UPX DLL imzalarını bozar, antivirüs yanlış pozitifini artırır).

### 2.1 Onay kapısı: `packaging/launcher.sha256`

Bu makinede gerçekten **açılmış** exe özeti depoya yazılır (`<64 hane> *KusursuzOCR.exe`). `build_exe.check_launcher_hash` derleme sonrası karşılaştırır:

- aynı: devam; farklı ya da dosya yok: **derleme ve yayın durur** (`SystemExit`);
- bilerek değiştirildiyse: `python build_installer.py --update-launcher-hash` (önce exe makinede açılır, sonra özet yazılır).

Release iş akışı da aynı kapıdan geçer (`build_installer.py`, `--no-verify` yok).

### 2.2 Testlerle sabitleme

`tests/test_release_packaging.py`: `launcher.py`, `launcher_version_info.txt` (LF'ye çevrilerek) ve `app_icon.ico` SHA-256 değerleri testte sabittir; PyInstaller bayrakları, `LAUNCHER_EPOCH`, kapı davranışı (farklı özet / onay yok / `update`), Inno ayarları ve yayın iş akışının kapıyı atlamadığı denetlenir.

## 3. Kurulum sihirbazı (Inno Setup 6): `packaging/KusursuzOCR.iss`

- `AppId` **sabit** (`D303C71B-...`; değişirse sonraki sürüm üstüne yazmaz). `build_installer.APP_ID` ile aynı olduğu testle denetlenir.
- `PrivilegesRequired=lowest`: UAC sormaz, güncelleme sessiz çalışır; `PrivilegesRequiredOverridesAllowed=dialog`.
- `CloseApplications=yes`, `RestartApplications=no`; yeniden açmayı `[Run]` içindeki `Check: RelaunchAfterUpdate` yapar: `WizardSilent and not HasParam('/VERYSILENT')`. Uygulama içi güncelleme `/SILENT` (ilerleme penceresi görünür, yeniden açılır), derleme sonrası deneme `/VERYSILENT` (açmaz).
- Çıktı adı sürümlüdür: `KusursuzOCR-Setup-X.Y.Z.exe`; güncelleyici bu desene bakar.
- Kullanıcı verisi (`~/.kusursuzocr`, EasyOCR model önbelleği) kaldırıcı tarafından silinmez.
- **Tesseract paketlenmez:** kullanıcı Tesseract'ı ayrıca kurmalıdır (`TesseractEngine` standart dizinleri otomatik arar). EasyOCR modelleri ilk kullanımda indirilir (internet gerekir).

## 4. Derleme ve doğrulama betikleri

| Dosya | Görev |
|---|---|
| `build_exe.py` | PyInstaller bağımsız değişkenleri, `LAUNCHER_EPOCH`, `check_launcher_hash` |
| `build_installer.py` | Tek komut: ISCC bul -> kararlı exe + kapı -> exe'yi bu makinede dene -> Inno derle -> kurulum dosyasını dene -> `.sha256` yaz. Seçenekler: `--skip-build`, `--no-verify` (CI'da `CI` ortam değişkeniyle otomatik), `--update-launcher-hash` |
| `build_verify.py` | `launch_check` (WinError 4551/1260 = SAC engeli), `installer_check` (geçici klasöre sessiz kurar, exe ve **kaldırıcıyı** dener) |
| `build_exe.bat` | `build_installer.py` için ince sarmalayıcı (eski `ocr_app.spec` kaldırıldı) |

**Gerçek kurulumu koruma:** deneme kurulumu gerçek kurulumla aynı `AppId`'yi kullanır; Inno aynı `HKCU\...\Uninstall\{AppId}_is1` kaydını ve Başlat menüsü kısayolunu yazar/siler. `save_registration` / `restore_registration` bunları yedekler ve `try/finally` ile her durumda geri yazar (`tests/test_build_verify.py`).

Exe denemesi başarısızsa `build_installer.py` durur (yeniden derlemek aynı exe'yi verir, döngü yok). Kurulum dosyası denemesi başarısızsa yalnızca uyarıdır (her sürümde yeni tek çalıştırılabilir dosya budur).

## 5. Exe'yi BİLEREK değiştirmek (nadir, dikkatli)

Gerekçeler: PyInstaller/Python yükseltme, simge, giriş betiği ya da sürüm kaynağı değişikliği. Derleme "özet DEĞİŞTİ" der ve durur.

1. Yeni exe'yi yerelde derle (`dist/` altında oluşur) ve **bu makinede aç**.
2. Engellendiyse **yalnızca** `LAUNCHER_EPOCH` değerini değiştir (tek yol), yeniden derle, tekrar dene.
3. Açılan özeti onayla: `python build_installer.py --update-launcher-hash`.
4. `tests/test_release_packaging.py` içindeki sabit özetleri (gerekirse) ve epoch değerini güncelle.
5. CI aynı özeti üretiyor mu? Üretmiyorsa kapı yayını durdurur; nedeni bul (Python/PyInstaller sürümü, satır sonu, yol). Bulunamıyorsa CI'ın exe'sini SAC'lı makinede indirip dene ve onayla.
6. Bu, tüm kullanıcılar için yeni exe demektir. Sık yapma.

## 6. YAPILMAMASI gerekenler

1. Her sürümde yeni exe özeti üretmek (güncelleme başarılı görünür, uygulama açılmaz).
2. Engellendi diye yeniden derleyip şansa güvenmek; "şu bayrakla geçer" aramak (deterministik tarif yok).
3. Kendi kendini kuran tek exe; yeniden açma için PowerShell/ek exe (yeni çalıştırılabilir dosya = yeni engel riski; yeniden açma Inno `[Run]` ile).
4. SAC'ı kapatmayı önermek / güvenlik ayarlarına dokunmak.
5. Inno kurulum dosyasını elle başlatıp öldürmek (yükseltilmiş sihirbaz öldürülemez, gerçek kayıt kalır); deneme yalnızca sessiz modda, geçici dizine, ardından kaldırıcı.
6. Deneme kurulumunu gerçek `AppId` ile yapıp kaydı yedeklememek; kaldırıcıyı denemeden bırakmak.
7. `PrivilegesRequired=admin` (Python'dan `CreateProcess` 740 verir).
8. UPX kullanmak; kapıyı atlamak (`--no-verify` ile yayın, özet dosyasını CI'da yeniden üretmek).
9. Kabuk heredoc'u ile kod yazmak (kaçışlar bozulur; dosya yazma aracı kullan).

## 7. Doğrulama durumu

Bkz. [[log]] en üst kayıt: hangi makinede, hangi özetle, kaç denemede doğrulandığı orada yazılır. **Henüz doğrulanmayanlar:** CI'da (`windows-latest`) derlenen exe özetinin yerel özetle aynı olduğu; indirilmiş (MOTW'li) kurulum dosyasının SAC'lı başka makinede açıldığı; gerçek bir Release üzerinden uygulama içi güncelleme (güncelleme deposu henüz tanımlı değil, bkz. [[update_system]]).
