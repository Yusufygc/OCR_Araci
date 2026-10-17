"""Güncelleme tercihleri (~/.kusursuzocr/updates.json): açılış denetimi ve atlanan sürüm."""
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from src.version import RELEASE_REPO, UPDATE_ENV_DISABLE

DEFAULT_PREFS_PATH = Path.home() / ".kusursuzocr" / "updates.json"


@dataclass
class UpdatePreferences:
    check_on_startup: bool = True
    skipped_version: str = ""


def load_preferences(path: Optional[Path] = None) -> UpdatePreferences:
    """Dosya yok/bozuksa varsayılanları döner (hiçbir zaman hata fırlatmaz)."""
    try:
        data = json.loads((path or DEFAULT_PREFS_PATH).read_text(encoding="utf-8"))
        return UpdatePreferences(
            check_on_startup=bool(data.get("check_on_startup", True)),
            skipped_version=str(data.get("skipped_version", "")),
        )
    except (OSError, ValueError, AttributeError):
        return UpdatePreferences()


def save_preferences(prefs: UpdatePreferences, path: Optional[Path] = None) -> bool:
    target = path or DEFAULT_PREFS_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(prefs), ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def is_update_check_disabled(environ=None) -> bool:
    """Ortam değişkeni ya da boş RELEASE_REPO güncelleme denetimini kapatır."""
    env = os.environ if environ is None else environ
    return env.get(UPDATE_ENV_DISABLE) == "1" or not RELEASE_REPO


def should_check_on_startup(prefs: UpdatePreferences, frozen: Optional[bool] = None) -> bool:
    """Açılış denetimi yalnızca paketlenmiş (exe) uygulamada, kapatılmamışsa yapılır."""
    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    return bool(is_frozen and prefs.check_on_startup and not is_update_check_disabled())
