from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QThread, Signal

from src.utils.updater import update_service
from src.utils.updater.update_service import UpdateError, UpdateInfo


class UpdateCheckWorker(QThread):
    """Arka planda `releases/latest` denetimi yapar; arayüzü bloklamaz."""
    update_found = Signal(object)  # UpdateInfo
    up_to_date = Signal()
    failed = Signal(str)

    def __init__(self, current_version: str, repo: str, service: Any = update_service, parent=None):
        super().__init__(parent)
        self._current_version = current_version
        self._repo = repo
        self._service = service

    def run(self):
        try:
            info: Optional[UpdateInfo] = self._service.check_for_update(self._current_version, self._repo)
        except UpdateError as error:
            self.failed.emit(str(error))
            return
        except Exception as error:  # ağ katmanındaki beklenmeyen hatalar arayüzü çökertmesin
            self.failed.emit(str(error))
            return
        if info is None:
            self.up_to_date.emit()
        else:
            self.update_found.emit(info)


class DownloadWorker(QThread):
    """Kurulum dosyasını doğrulayarak indirir; ilerleme sinyali yayar."""
    progress = Signal(int, int)
    finished_ok = Signal(str)  # indirilen dosyanın yolu
    failed = Signal(str)

    def __init__(self, info: UpdateInfo, dest_dir: Path, service: Any = update_service, parent=None):
        super().__init__(parent)
        self._info = info
        self._dest_dir = dest_dir
        self._service = service

    def run(self):
        try:
            path = self._service.download_installer(
                self._info, self._dest_dir, progress=lambda done, total: self.progress.emit(done, total)
            )
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished_ok.emit(str(path))
