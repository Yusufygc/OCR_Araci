"""
Kararlı exe derleyicisi (PyInstaller, --onedir, --debug=noarchive).

Exe her sürümde bayt bayt aynı kalır: sabit giriş betiği, sabit sürüm kaynağı, sabit SOURCE_DATE_EPOCH.
Sürümle değişen uygulama kodu exe'nin dışında `.pyc` olarak durur.
Exe ikonu (packaging/app_icon.ico) exe özetine girer; pencere ikonu (src/ui/assets) veri dosyası olarak dışarıda kalır. Gerekçe: docs/wiki/exe_distribution.md
"""
import hashlib
import os
import sys
from pathlib import Path
from typing import List, Optional

from src.version import EXE_NAME

ROOT = Path(__file__).resolve().parent
LAUNCHER_EPOCH = 1700000000  # DEĞİŞTİRME (bilerek yeni özet denemek için tek yol: docs/wiki/exe_distribution.md)
LAUNCHER_HASH_FILE = ROOT / "packaging" / "launcher.sha256"
HIDDEN_IMPORTS = (
    "easyocr", "torch", "torchvision", "skimage", "skimage.io", "scipy",
    "PIL", "cv2", "numpy", "docx", "lxml", "lxml._elementpath", "lxml.etree",
)
EXCLUDED_MODULES = ("matplotlib", "tkinter", "IPython", "jupyter", "notebook", "pytest")


def exe_path(root: Path = ROOT) -> Path:
    """Derlenen kararlı exe'nin yolu."""
    return root / "dist" / EXE_NAME / f"{EXE_NAME}.exe"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pyinstaller_arguments(root: Path = ROOT) -> List[str]:
    """PyInstaller bağımsız değişkenleri (kararlı exe için hepsi gerekli)."""
    arguments = [
        str(root / "packaging" / "launcher.py"),
        f"--paths={root}",
        f"--name={EXE_NAME}",
        "--onedir", "--windowed", "--clean", "--noconfirm",
        "--noupx",
        "--debug=noarchive",
        f"--version-file={root / 'packaging' / 'launcher_version_info.txt'}",
        f"--icon={root / 'packaging' / 'app_icon.ico'}",
        f"--add-data={root / 'src' / 'ui' / 'assets'}{os.pathsep}src/ui/assets",
        f"--distpath={root / 'dist'}",
        f"--workpath={root / 'build'}",
        f"--specpath={root / 'build'}",
        "--collect-submodules=src",
        "--collect-data=easyocr",
        "--collect-submodules=easyocr",
    ]
    arguments += [f"--hidden-import={name}" for name in HIDDEN_IMPORTS]
    arguments += [f"--exclude-module={name}" for name in EXCLUDED_MODULES]
    return arguments


def build_executable(root: Path = ROOT, verify_hash: bool = True) -> Path:
    """Exe'yi derler; verify_hash açıkken onaylı özetle karşılaştırır (farklıysa durur)."""
    import PyInstaller.__main__ as pyinstaller_main

    os.environ["SOURCE_DATE_EPOCH"] = str(LAUNCHER_EPOCH)
    pyinstaller_main.run(pyinstaller_arguments(root))
    exe = exe_path(root)
    if verify_hash:
        check_launcher_hash(exe)
    return exe


def check_launcher_hash(exe: Path, hash_file: Path = LAUNCHER_HASH_FILE, update: bool = False) -> str:
    """Exe özetini onaylı özetle karşılaştırır. Farklı ya da onay yoksa SystemExit ile durur."""
    actual = file_sha256(exe)
    if update:
        hash_file.write_text(f"{actual} *{exe.name}\n", encoding="ascii")
        print(f"Kararlı exe özeti onaylandı: {actual}")
        return actual

    approved = _read_approved_hash(hash_file)
    if approved is None:
        sys.exit(f"HATA: {hash_file.name} yok. Exe'yi bu makinede açıp `python build_installer.py --update-launcher-hash` ile onayla.")
    if approved != actual:
        sys.exit(_hash_mismatch_message(approved, actual))
    print(f"Kararlı exe özeti onaylananla aynı: {actual}")
    return actual


def _read_approved_hash(hash_file: Path) -> Optional[str]:
    if not hash_file.exists():
        return None
    parts = hash_file.read_text(encoding="ascii").split()
    return parts[0].lower() if parts else None


def _hash_mismatch_message(approved: str, actual: str) -> str:
    return (
        "HATA: Kararlı exe özeti DEĞİŞTİ; kullanıcıya onaysız, engellenebilecek yeni bir exe gitmesin diye durduruldu.\n"
        f"  onaylı : {approved}\n  yeni   : {actual}\n"
        "Nedenler: PyInstaller/Python sürümü, packaging/ dosyaları, satır sonları. Bilerek değiştirdiysen "
        "docs/wiki/exe_distribution.md bölüm 'Exe'yi bilerek değiştirmek' adımlarını izle."
    )


if __name__ == "__main__":
    build_executable()
