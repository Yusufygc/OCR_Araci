"""
Uygulama içi güncelleme çekirdeği (UI'dan bağımsız).

Akış: GitHub `releases/latest` denetimi -> sürüm karşılaştırma -> doğrulamalı indirme -> kurulum dosyasını başlatma.
Güvenlik: adres yalnızca github.com, sıkı dosya adı, boyut sınırı, zorunlu SHA-256 (yoksa güncelleme reddedilir).
Gerekçe ve sınırlar: docs/wiki/update_system.md
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from src.version import INSTALLER_PREFIX

API_URL = "https://api.github.com/repos/{repo}/releases/latest"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")
INSTALLER_NAME_PATTERN = re.compile(rf"^{re.escape(INSTALLER_PREFIX)}-Setup-(\d+\.\d+\.\d+)\.exe$")
SHA256_PATTERN = re.compile(r"\b[0-9a-fA-F]{64}\b")

MAX_API_BYTES = 1024 * 1024
MAX_CHECKSUM_BYTES = 4096
MAX_NOTES_CHARS = 4000
# GitHub Release dosya sınırı 2 GiB; torch/EasyOCR içeren kurulum dosyası yüzlerce MB olabilir.
MAX_INSTALLER_BYTES = 2 * 1024 ** 3
CHUNK_BYTES = 256 * 1024
REQUEST_TIMEOUT_S = 15
SAC_BLOCK_WINERRORS = (4551, 1260)
INSTALLER_ARGS = ("/SILENT", "/SUPPRESSMSGBOXES", "/CLOSEAPPLICATIONS")

Opener = Callable[..., object]
ProgressCallback = Callable[[int, int], None]


class UpdateError(Exception):
    """Güncelleme denetimi / indirmesi başarısız oldu (mesaj kullanıcıya gösterilebilir)."""


class InstallerBlockedError(UpdateError):
    """Windows (Akıllı Uygulama Denetimi) kurulum dosyasını başlatmadı."""


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    tag: str
    installer_name: str
    download_url: str
    size: int
    sha256: Optional[str]
    checksum_url: Optional[str]
    notes: str
    page_url: str


def parse_version(text: str) -> Optional[Tuple[int, int, int]]:
    """'v1.2.3' / '1.2.3' -> (1, 2, 3); ön sürüm ('1.2.3-rc1') ve geçersiz biçim None döner."""
    match = VERSION_PATTERN.match(str(text).strip())
    return tuple(int(part) for part in match.groups()) if match else None  # type: ignore[return-value]


def is_valid_repo(repo: str) -> bool:
    """'sahip/depo' biçimi; '.' ve '..' parçaları (yol atlatma) reddedilir."""
    if not REPO_PATTERN.match(repo or ""):
        return False
    return all(part not in (".", "..") for part in repo.split("/"))


def is_allowed_host(url: str) -> bool:
    """Yalnızca https ve github.com / *.githubusercontent.com adreslerine izin verilir."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        return False
    return host == "github.com" or host.endswith(".githubusercontent.com")


def _is_release_download_url(url: str, repo: str) -> bool:
    prefix = f"https://github.com/{repo}/releases/download/"
    return url.startswith(prefix) and is_allowed_host(url)


class _HostCheckingRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Yönlendirme izin verilmeyen bir host'a giderse isteği keser."""

    def redirect_request(self, *args):
        newurl = args[-1]  # (req, fp, code, msg, headers, newurl)
        host = urllib.parse.urlparse(newurl).hostname
        if not is_allowed_host(newurl) and host != "api.github.com":
            raise UpdateError(f"İzin verilmeyen yönlendirme reddedildi: {host}")
        return super().redirect_request(*args)


def default_opener(request, timeout: float = REQUEST_TIMEOUT_S):
    """Kimlik bilgisi göndermeyen, yönlendirme host'unu denetleyen varsayılan HTTP açıcı."""
    return urllib.request.build_opener(_HostCheckingRedirectHandler).open(request, timeout=timeout)


def _request(url: str, opener: Optional[Opener]):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "KusursuzOCR-Updater"}
    return (opener or default_opener)(urllib.request.Request(url, headers=headers), timeout=REQUEST_TIMEOUT_S)


def fetch_latest_release(repo: str, opener: Optional[Opener] = None) -> dict:
    """GitHub `releases/latest` yanıtını döner. Ağ/biçim hatasında UpdateError fırlatır."""
    if not is_valid_repo(repo):
        raise UpdateError("Güncelleme deposu ayarlanmamış ya da geçersiz.")
    try:
        response = _request(API_URL.format(repo=repo), opener)
        raw = response.read(MAX_API_BYTES + 1)  # type: ignore[attr-defined]
    except (urllib.error.URLError, OSError) as error:
        raise UpdateError(f"Güncelleme sunucusuna ulaşılamadı: {error}") from error
    if len(raw) > MAX_API_BYTES:
        raise UpdateError("Güncelleme yanıtı beklenenden büyük.")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UpdateError("Güncelleme yanıtı okunamadı.") from error
    if not isinstance(data, dict):
        raise UpdateError("Güncelleme yanıtı geçersiz.")
    return data


def _find_installer_asset(release: dict, version_text: str, repo: str) -> Optional[dict]:
    for asset in release.get("assets") or []:
        match = INSTALLER_NAME_PATTERN.match(str(asset.get("name", "")))
        url = str(asset.get("browser_download_url", ""))
        if match and match.group(1) == version_text and _is_release_download_url(url, repo):
            return asset
    return None


def _digest_of(asset: dict) -> Optional[str]:
    digest = str(asset.get("digest") or "")
    if digest.lower().startswith("sha256:") and SHA256_PATTERN.fullmatch(digest[7:]):
        return digest[7:].lower()
    return None


def _checksum_url_of(release: dict, asset: dict, repo: str) -> Optional[str]:
    wanted = f"{asset['name']}.sha256"
    for other in release.get("assets") or []:
        url = str(other.get("browser_download_url", ""))
        if other.get("name") == wanted and _is_release_download_url(url, repo):
            return url
    return None


def _newer_version(release: dict, current_version: str) -> Optional[Tuple[int, int, int]]:
    """Yayın taslak/ön sürüm değilse ve yüklü sürümden yeniyse sürüm üçlüsünü döner."""
    if release.get("draft") or release.get("prerelease"):
        return None
    latest, current = parse_version(str(release.get("tag_name", ""))), parse_version(current_version)
    if latest is None or current is None or latest <= current:
        return None
    return latest


def release_to_update(release: dict, current_version: str, repo: str) -> Optional[UpdateInfo]:
    """Yayın, yüklü sürümden yeniyse ve geçerli kurulum dosyası içeriyorsa UpdateInfo döner."""
    latest = _newer_version(release, current_version)
    if latest is None:
        return None
    version_text = ".".join(str(part) for part in latest)
    asset = _find_installer_asset(release, version_text, repo)
    if asset is None:
        return None
    return UpdateInfo(
        version=version_text,
        tag=str(release["tag_name"]),
        installer_name=str(asset["name"]),
        download_url=str(asset["browser_download_url"]),
        size=int(asset.get("size") or 0),
        sha256=_digest_of(asset),
        checksum_url=_checksum_url_of(release, asset, repo),
        notes=str(release.get("body") or "")[:MAX_NOTES_CHARS],
        page_url=str(release.get("html_url") or f"https://github.com/{repo}/releases/latest"),
    )


def check_for_update(current_version: str, repo: str, opener: Optional[Opener] = None) -> Optional[UpdateInfo]:
    """Yeni sürüm varsa UpdateInfo, yoksa None. Hata durumunda UpdateError."""
    return release_to_update(fetch_latest_release(repo, opener), current_version, repo)


def resolve_sha256(info: UpdateInfo, opener: Optional[Opener] = None) -> str:
    """Özeti GitHub `digest` alanından, yoksa `.sha256` dosyasından alır; ikisi de yoksa reddeder."""
    if info.sha256:
        return info.sha256
    if not info.checksum_url:
        raise UpdateError("Sürüm için SHA-256 özeti yok; güvenlik nedeniyle güncelleme reddedildi.")
    try:
        response = _request(info.checksum_url, opener)
        final_url = response.geturl() if hasattr(response, "geturl") else info.checksum_url
        if not is_allowed_host(final_url):
            raise UpdateError("Özet dosyası izin verilmeyen bir adresten geldi.")
        text = response.read(MAX_CHECKSUM_BYTES).decode("ascii", errors="ignore")  # type: ignore[attr-defined]
    except (urllib.error.URLError, OSError) as error:
        raise UpdateError(f"SHA-256 özeti indirilemedi: {error}") from error
    match = SHA256_PATTERN.search(text)
    if not match:
        raise UpdateError("SHA-256 özet dosyası geçersiz.")
    return match.group(0).lower()


def _validated_installer_name(info: UpdateInfo) -> str:
    name = Path(info.installer_name).name
    if name != info.installer_name or not INSTALLER_NAME_PATTERN.match(name):
        raise UpdateError("Kurulum dosyası adı beklenen biçimde değil.")
    if not is_allowed_host(info.download_url):
        raise UpdateError("İndirme adresi izin verilmeyen bir host'a işaret ediyor.")
    if info.size <= 0 or info.size > MAX_INSTALLER_BYTES:
        raise UpdateError("Kurulum dosyası boyutu geçersiz.")
    return name


def download_installer(
    info: UpdateInfo,
    dest_dir: Path,
    progress: Optional[ProgressCallback] = None,
    opener: Optional[Opener] = None,
) -> Path:
    """Kurulum dosyasını indirir; ad, adres, boyut ve SHA-256 doğrulanır. Uyuşmazlıkta dosya silinir."""
    name = _validated_installer_name(info)
    expected_sha = resolve_sha256(info, opener)
    dest_dir.mkdir(parents=True, exist_ok=True)
    target, partial = dest_dir / name, dest_dir / (name + ".part")
    try:
        actual_sha = _stream_to_file(info, partial, progress, opener)
        if actual_sha != expected_sha:
            raise UpdateError("İndirilen dosyanın SHA-256 özeti uyuşmuyor; dosya silindi.")
        os.replace(partial, target)
    finally:
        if partial.exists():
            partial.unlink()
    return target


def _stream_to_file(info: UpdateInfo, partial: Path, progress: Optional[ProgressCallback], opener: Optional[Opener]) -> str:
    try:
        response = _request(info.download_url, opener)
    except (urllib.error.URLError, OSError) as error:
        raise UpdateError(f"Kurulum dosyası indirilemedi: {error}") from error
    final_url = response.geturl() if hasattr(response, "geturl") else info.download_url
    if not is_allowed_host(final_url):
        raise UpdateError("İndirme izin verilmeyen bir adrese yönlendi.")
    digest, written = hashlib.sha256(), 0
    with open(partial, "wb") as handle:
        while True:
            chunk = response.read(CHUNK_BYTES)  # type: ignore[attr-defined]
            if not chunk:
                break
            written += len(chunk)
            if written > min(info.size, MAX_INSTALLER_BYTES):
                raise UpdateError("İndirilen dosya Release'teki boyuttan büyük.")
            digest.update(chunk)
            handle.write(chunk)
            if progress:
                progress(written, info.size)
    if written != info.size:
        raise UpdateError("İndirilen dosya boyutu Release'teki boyutla eşleşmiyor.")
    return digest.hexdigest()


def installer_arguments(log_path: Optional[Path] = None) -> List[str]:
    args = list(INSTALLER_ARGS)
    if log_path is not None:
        args.append(f"/LOG={log_path}")
    return args


def launch_installer(
    installer: Path,
    log_path: Optional[Path] = None,
    spawn: Callable[..., object] = subprocess.Popen,
    shell_execute: Optional[Callable[[str, str], int]] = None,
) -> None:
    """Kurulumu bağımsız süreçte başlatır. SAC engelinde Gezgin yolunu dener; ikisi de engelliyse InstallerBlockedError."""
    if sys.platform != "win32" and spawn is subprocess.Popen:
        raise UpdateError("Uygulama içi kurulum yalnızca Windows'ta çalışır.")
    if not INSTALLER_NAME_PATTERN.match(installer.name):
        raise UpdateError("Kurulum dosyası adı beklenen biçimde değil.")
    args = installer_arguments(log_path)
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        spawn([str(installer), *args], creationflags=flags, close_fds=True,
              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except OSError as error:
        if getattr(error, "winerror", None) not in SAC_BLOCK_WINERRORS:
            raise UpdateError(f"Kurulum başlatılamadı: {error}") from error
    _launch_via_shell(installer, " ".join(args), shell_execute)


def _launch_via_shell(installer: Path, params: str, shell_execute: Optional[Callable[[str, str], int]]) -> None:
    runner = shell_execute or _default_shell_execute
    if runner(str(installer), params) <= 32:
        raise InstallerBlockedError("Windows kurulum dosyasını şimdilik engelledi.")


def _default_shell_execute(path: str, params: str) -> int:
    import ctypes

    return int(ctypes.windll.shell32.ShellExecuteW(None, "open", path, params, None, 1))  # type: ignore[attr-defined]
