"""
Sürüm yükseltir: src/version.py günceller, commit atar, ek açıklamalı etiket oluşturur. HİÇBİR ŞEY GÖNDERMEZ.

    python tools/release.py 1.0.1
    python tools/release.py --check-tag v1.0.1     # CI: etiket ile src/version.py uyumunu denetler

Sonra elle: git push origin <dal>  ve  git push origin vX.Y.Z   (--follow-tags KULLANMA)
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "src" / "version.py"
VERSION_LINE = re.compile(r'^__version__ = "(\d+\.\d+\.\d+)"$', re.MULTILINE)
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
RELEASE_BRANCHES = ("main", "master")


def parse_version(text: str) -> Tuple[int, int, int]:
    if not SEMVER.match(text):
        raise ValueError(f"Sürüm MAJOR.MINOR.PATCH biçiminde olmalı: {text!r}")
    major, minor, patch = (int(part) for part in text.split("."))
    return major, minor, patch


def read_version(path: Path = VERSION_FILE) -> str:
    match = VERSION_LINE.search(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{path} içinde __version__ bulunamadı")
    return match.group(1)


def write_version(version: str, path: Path = VERSION_FILE) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(VERSION_LINE.sub(f'__version__ = "{version}"', text), encoding="utf-8")


def check_tag(tag: str, path: Path = VERSION_FILE) -> None:
    """Etiket `v` + __version__ ile birebir aynı olmalı; değilse hata fırlatır."""
    expected = f"v{read_version(path)}"
    if tag != expected:
        raise ValueError(f"Etiket ({tag}) ile src/version.py ({expected}) farklı")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def ensure_releasable(new_version: str) -> None:
    """Çalışma ağacı temiz, dal main/master, sürüm mevcuttan büyük, etiket yok."""
    if git("status", "--porcelain"):
        raise ValueError("Çalışma ağacı temiz değil; önce commit'le")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch not in RELEASE_BRANCHES:
        raise ValueError(f"Dal {' veya '.join(RELEASE_BRANCHES)} olmalı (şu an: {branch})")
    if parse_version(new_version) <= parse_version(read_version()):
        raise ValueError(f"Yeni sürüm ({new_version}) mevcuttan ({read_version()}) büyük olmalı")
    if git("tag", "--list", f"v{new_version}"):
        raise ValueError(f"v{new_version} etiketi zaten var")


def release(new_version: str) -> None:
    ensure_releasable(new_version)
    write_version(new_version)
    git("add", str(VERSION_FILE))
    git("commit", "-m", f"chore(release): v{new_version}")
    git("tag", "-a", f"v{new_version}", "-m", f"Sürüm {new_version}")
    print(f"v{new_version} commit'i ve etiketi oluşturuldu (gönderilmedi).")
    print(f"Sonra: git push origin {git('rev-parse', '--abbrev-ref', 'HEAD')}  ve  git push origin v{new_version}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("version", nargs="?")
    parser.add_argument("--check-tag", metavar="vX.Y.Z")
    args = parser.parse_args(argv)
    try:
        if args.check_tag:
            check_tag(args.check_tag)
        elif args.version:
            release(args.version)
        else:
            parser.error("sürüm ya da --check-tag gerekli")
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"HATA: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
