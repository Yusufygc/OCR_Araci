"""
Tek komutla kararlı exe + Inno kurulum dosyası + .sha256 üretir.

    python build_installer.py                         # derle, bu makinede dene, kurulum dosyasını yaz
    python build_installer.py --skip-build            # mevcut dist/ ile yalnızca kurulum dosyası
    python build_installer.py --no-verify             # makinede deneme yok (CI'da otomatik)
    python build_installer.py --update-launcher-hash  # bilerek değişen exe özetini onayla
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import build_exe
import build_verify
from src.version import EXE_NAME, INSTALLER_PREFIX, UPDATE_ENV_DISABLE, __version__

ROOT = build_exe.ROOT
ISS_FILE = ROOT / "packaging" / "OCRAraci.iss"
INSTALLER_DIR = ROOT / "dist" / "installer"
APP_ID = "D303C71B-3E64-4B0C-8342-118BE7BA81E2"  # packaging/OCRAraci.iss ile aynı (testle denetlenir)


def find_iscc() -> Optional[str]:
    """Inno Setup derleyicisini (ISCC.exe) bulur."""
    found = shutil.which("ISCC")
    if found:
        return found
    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    return next((str(path) for path in candidates if path.exists()), None)


def installer_path(version: str = __version__) -> Path:
    return INSTALLER_DIR / f"{INSTALLER_PREFIX}-Setup-{version}.exe"


def compile_installer(iscc: str, version: str = __version__) -> Path:
    """Inno ile kurulum dosyasını derler (argüman doğrudan verilir: git-bash '/D' yol çevirisi sorunu yok)."""
    subprocess.run([iscc, f"/DAppVersion={version}", str(ISS_FILE)], check=True)
    return installer_path(version)


def write_checksum(installer: Path) -> Path:
    checksum = installer.with_name(installer.name + ".sha256")
    checksum.write_text(f"{build_exe.file_sha256(installer)} *{installer.name}\n", encoding="ascii")
    return checksum


def selftest_executable(exe: Path) -> None:
    """Exe'nin çalışma zamanı bağımlılıklarını başsız sınar (CI dahil her zaman çalışır)."""
    try:
        passed, report = build_verify.selftest_check(exe)
    except build_verify.LaunchBlockedError as error:
        sys.exit(f"HATA: {error}. docs/wiki/exe_distribution.md: 'Exe'yi bilerek değiştirmek' (LAUNCHER_EPOCH).")
    print(report)
    if not passed:
        sys.exit("HATA: exe --selftest başarısız (eksik binary/modül). Rapor yukarıda.")


def verify_executable(exe: Path) -> None:
    """Exe'yi bu makinede dener; başarısızsa durur (yeniden derlemek aynı exe'yi verir: döngü yok)."""
    try:
        alive = build_verify.launch_check(exe, env_extra={UPDATE_ENV_DISABLE: "1"})
    except build_verify.LaunchBlockedError as error:
        sys.exit(f"HATA: {error}. docs/wiki/exe_distribution.md: 'Exe'yi bilerek değiştirmek' (LAUNCHER_EPOCH).")
    if not alive:
        sys.exit("HATA: exe açıldı ama hemen kapandı. Günlükleri kontrol et.")
    print("Exe bu makinede açıldı.")


def verify_installer(installer: Path) -> None:
    """Kurulum dosyasını dener; başarısızlık yalnızca uyarıdır (her sürümde yeni tek çalıştırılabilir dosya)."""
    programs = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    try:
        spec = build_verify.InstallerCheckSpec(
            APP_ID, f"{EXE_NAME}.exe", [programs / "OCR Aracı.lnk"], {UPDATE_ENV_DISABLE: "1"}
        )
        build_verify.installer_check(installer, spec)
        print("Kurulum dosyası bu makinede kuruldu, açıldı ve kaldırıldı.")
    except (build_verify.LaunchBlockedError, RuntimeError, OSError) as error:
        print(f"UYARI: kurulum dosyası denemesi başarısız: {error}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--no-verify", action="store_true")
    parser.add_argument("--update-launcher-hash", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    iscc = find_iscc()
    if iscc is None:
        sys.exit("HATA: Inno Setup 6 (ISCC.exe) bulunamadı. Kur: choco install innosetup -y")

    exe = build_exe.exe_path()
    if not args.skip_build:
        build_exe.build_executable(verify_hash=False)
    selftest_executable(exe)
    verify = not (args.no_verify or os.environ.get("CI"))
    if verify and args.update_launcher_hash:
        verify_executable(exe)  # özeti onaylamadan önce bu makinede açıldığından emin ol
    build_exe.check_launcher_hash(exe, update=args.update_launcher_hash)
    if verify and not args.update_launcher_hash:
        verify_executable(exe)

    installer = compile_installer(iscc)
    if verify:
        verify_installer(installer)
    print(f"Kurulum dosyası: {installer}\nÖzet dosyası  : {write_checksum(installer)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
