"""
Derleme sonrası doğrulama (yalnızca standart kitaplık; başka projeye kopyalanabilir).

- launch_check: exe'yi başlatır, Akıllı Uygulama Denetimi (SAC) engelini yakalar.
- installer_check: kurulum dosyasını geçici klasöre sessizce kurar, exe'yi ve kaldırıcıyı dener.
  Gerçek kurulumun kaydı ve kısayolu yedeklenir, her durumda geri yazılır.
"""
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

SAC_BLOCK_WINERRORS = (4551, 1260)
LAUNCH_SECONDS = 8


class LaunchBlockedError(RuntimeError):
    """Windows (Akıllı Uygulama Denetimi) dosyayı çalıştırmadı."""


def launch_check(exe: Path, seconds: int = LAUNCH_SECONDS, env_extra: Optional[Dict[str, str]] = None) -> bool:
    """Exe'yi başlatır; süre sonunda hâlâ çalışıyorsa True döner ve süreci kapatır."""
    env = dict(os.environ, **(env_extra or {}))
    try:
        proc = subprocess.Popen([str(exe)], env=env, cwd=str(exe.parent))
    except OSError as error:
        if getattr(error, "winerror", None) in SAC_BLOCK_WINERRORS:
            raise LaunchBlockedError(f"{exe.name} engellendi (WinError {error.winerror})") from error
        raise
    time.sleep(seconds)
    alive = proc.poll() is None
    if alive:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
    return alive


def selftest_check(exe: Path, timeout: int = 300) -> Tuple[bool, str]:
    """`exe --selftest` çalıştırır; (başarılı mı, rapor) döner. Hata penceresi açık kalsa bile yakalar."""
    report_path = Path(tempfile.mkdtemp(prefix="selftest_")) / "rapor.txt"
    env = dict(os.environ, OCRARACI_SELFTEST_OUT=str(report_path))
    try:
        result = subprocess.run([str(exe), "--selftest"], env=env, cwd=str(exe.parent), timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return False, f"Zaman aşımı ({timeout} sn): exe --selftest bitmedi (hata penceresi açık kalmış olabilir)"
    except OSError as error:
        if getattr(error, "winerror", None) in SAC_BLOCK_WINERRORS:
            raise LaunchBlockedError(f"{exe.name} engellendi (WinError {error.winerror})") from error
        raise
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else "(rapor dosyası oluşmadı)"
    shutil.rmtree(report_path.parent, ignore_errors=True)
    return result.returncode == 0, report


# --- Gerçek kurulumu koruma: deneme kurulumu aynı AppId'yi kullanır ---

def uninstall_key_path(app_id: str) -> str:
    return rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{{{app_id}}}_is1"


def save_registration(app_id: str, shortcut_paths: List[Path]) -> dict:
    """Kayıt defteri değerlerini ve kısayol baytlarını yedekler."""
    import winreg

    values: Optional[List[Tuple[str, object, int]]] = None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uninstall_key_path(app_id)) as key:
            values, index = [], 0
            while True:
                try:
                    values.append(winreg.EnumValue(key, index))
                except OSError:
                    break
                index += 1
    except FileNotFoundError:
        values = None
    shortcuts = {str(p): (p.read_bytes() if p.exists() else None) for p in shortcut_paths}
    return {"app_id": app_id, "values": values, "shortcuts": shortcuts}


def restore_registration(snapshot: dict) -> None:
    """Yedeği geri yazar; yedekte kayıt yoksa deneme kurulumunun bıraktığını siler."""
    import winreg

    path = uninstall_key_path(snapshot["app_id"])
    if snapshot["values"] is None:
        _delete_key_quietly(path)
    else:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_ALL_ACCESS) as key:
            _clear_values(key)
            for name, value, kind in snapshot["values"]:
                winreg.SetValueEx(key, name, 0, kind, value)
    for raw_path, data in snapshot["shortcuts"].items():
        _restore_shortcut(Path(raw_path), data)


def _clear_values(key) -> None:
    import winreg

    while True:
        try:
            name = winreg.EnumValue(key, 0)[0]
        except OSError:
            return
        winreg.DeleteValue(key, name)


def _delete_key_quietly(path: str) -> None:
    import winreg

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def _restore_shortcut(path: Path, data: Optional[bytes]) -> None:
    if data is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


@dataclass
class InstallerCheckSpec:
    """Kurulum dosyası denemesi ayarları (save/restore testte taklit edilebilir)."""
    app_id: str
    exe_name: str
    shortcut_paths: List[Path] = field(default_factory=list)
    env_extra: Optional[Dict[str, str]] = None
    save: Callable[[str, List[Path]], dict] = save_registration
    restore: Callable[[dict], None] = restore_registration


def installer_check(installer: Path, spec: InstallerCheckSpec) -> None:
    """Kurulum dosyasını geçici klasöre sessizce kurar, exe ve kaldırıcıyı dener, her şeyi temizler."""
    snapshot = spec.save(spec.app_id, spec.shortcut_paths)
    target = Path(tempfile.mkdtemp(prefix="installer_check_"))
    try:
        _silent_install(installer, target)
        passed, report = selftest_check(target / spec.exe_name)
        if not passed:
            raise RuntimeError(f"Kurulan {spec.exe_name} --selftest başarısız:\n{report}")
        if not launch_check(target / spec.exe_name, env_extra=spec.env_extra):
            raise RuntimeError(f"Kurulan {spec.exe_name} açılıp kapandı")
        _silent_uninstall(target)
    finally:
        spec.restore(snapshot)
        shutil.rmtree(target, ignore_errors=True)
        target.with_name(target.name + ".log").unlink(missing_ok=True)


def _silent_install(installer: Path, target: Path) -> None:
    command = [
        str(installer), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER",
        f"/DIR={target}", f"/LOG={target.parent / (target.name + '.log')}",
    ]
    _run_checked(command, "Sessiz kurulum")


def _silent_uninstall(target: Path) -> None:
    uninstaller = target / "unins000.exe"
    if not uninstaller.exists():
        raise RuntimeError("Kaldırıcı (unins000.exe) kurulmadı")
    _run_checked([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], "Kaldırıcı")


def _run_checked(command: List[str], label: str) -> None:
    try:
        result = subprocess.run(command, capture_output=True, timeout=900, check=False)
    except OSError as error:
        if getattr(error, "winerror", None) in SAC_BLOCK_WINERRORS:
            raise LaunchBlockedError(f"{label} engellendi (WinError {error.winerror})") from error
        raise
    if result.returncode != 0:
        raise RuntimeError(f"{label} başarısız (çıkış kodu {result.returncode})")
