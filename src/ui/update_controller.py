import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import QMenuBar, QMessageBox, QWidget

from src.ui.components.update_dialog import UpdateDialog
from src.ui.strings import UIStrings
from src.ui.workers.update_workers import DownloadWorker, UpdateCheckWorker
from src.utils.updater import update_prefs, update_service
from src.utils.updater.update_service import InstallerBlockedError, UpdateError, UpdateInfo
from src import version as app_version

STARTUP_CHECK_DELAY_MS = 3000
RETRY_INTERVAL_MS = 15000
MAX_RETRIES = 40
UPDATE_DIR_NAME = f"{app_version.EXE_NAME}Update"


def _reveal_in_explorer(path: Path) -> None:
    """Dosyayı Gezgin'de seçili gösterir (yalnızca Windows)."""
    if os.name == "nt":
        subprocess.Popen(["explorer", f"/select,{path}"])


@dataclass
class UpdateSettings:
    """UpdateController ayarları; boş bırakılanlar uygulama varsayılanlarını kullanır (testte değiştirilebilir)."""
    repo: str = app_version.RELEASE_REPO
    current_version: str = app_version.__version__
    prefs_path: Optional[Path] = None
    download_dir: Path = field(default_factory=lambda: Path(tempfile.gettempdir()) / UPDATE_DIR_NAME)
    retry_interval_ms: int = RETRY_INTERVAL_MS
    reveal: Callable[[Path], None] = _reveal_in_explorer
    open_url: Callable[[str], object] = lambda url: QDesktopServices.openUrl(QUrl(url))


class UpdateController(QObject):
    """
    Uygulama içi güncelleme akışını yönetir: denetim, diyalog, indirme, kurulum ve Windows engeli için yeniden deneme.
    Ağ/dosya işleri `update_service` (birim testli) ve worker thread'lerindedir.
    """
    quit_requested = Signal()

    def __init__(self, parent: QWidget, service: Any = update_service, settings: Optional[UpdateSettings] = None):
        super().__init__(parent)
        cfg = settings or UpdateSettings()
        self._window, self._service = parent, service
        self._repo, self._current = cfg.repo, cfg.current_version
        self._prefs_path = cfg.prefs_path
        self._download_dir = cfg.download_dir
        self._retry_interval_ms = cfg.retry_interval_ms
        self._reveal, self._open_url = cfg.reveal, cfg.open_url
        self._prefs = update_prefs.load_preferences(cfg.prefs_path)
        self._dialog: Optional[UpdateDialog] = None
        self._check_worker: Optional[UpdateCheckWorker] = None
        self._download_worker: Optional[DownloadWorker] = None
        self._installer: Optional[Path] = None
        self._attempt = 0
        self._manual = False

    # --- Menü ve tetikleme ---

    def install_menu(self, menu_bar: QMenuBar) -> None:
        menu = menu_bar.addMenu(UIStrings.MENU_HELP)
        act_version = QAction(UIStrings.ACT_VERSION.format(version=self._current), menu)
        act_version.setEnabled(False)
        self.act_check = QAction(UIStrings.ACT_CHECK_UPDATES, menu)
        self.act_check.triggered.connect(lambda: self.check(manual=True))
        self.act_auto = QAction(UIStrings.ACT_AUTO_CHECK, menu)
        self.act_auto.setCheckable(True)
        self.act_auto.setChecked(self._prefs.check_on_startup)
        self.act_auto.toggled.connect(self._on_auto_toggled)
        for action in (act_version, self.act_check, self.act_auto):
            menu.addAction(action)

    def schedule_startup_check(self) -> None:
        """Pencere çizildikten sonra bir kez denetler (yalnızca paketlenmiş uygulamada, kapatılmadıysa)."""
        if update_prefs.should_check_on_startup(self._prefs):
            QTimer.singleShot(STARTUP_CHECK_DELAY_MS, lambda: self.check(manual=False))

    def _on_auto_toggled(self, checked: bool) -> None:
        self._prefs.check_on_startup = checked
        update_prefs.save_preferences(self._prefs, self._prefs_path)

    # --- Denetim ---

    def check(self, manual: bool) -> None:
        self._manual = manual
        if not self._repo:
            if manual:
                QMessageBox.information(self._window, UIStrings.UPDATE_TITLE, UIStrings.UPDATE_NO_REPO)
            return
        if self._check_worker is not None and self._check_worker.isRunning():
            return
        worker = UpdateCheckWorker(self._current, self._repo, self._service, parent=self)
        worker.update_found.connect(self._on_update_found)
        worker.up_to_date.connect(self._on_up_to_date)
        worker.failed.connect(self._on_check_failed)
        self._check_worker = worker
        worker.start()

    def _on_up_to_date(self) -> None:
        if self._manual:
            QMessageBox.information(
                self._window, UIStrings.UPDATE_TITLE, UIStrings.UPDATE_UP_TO_DATE.format(version=self._current)
            )

    def _on_check_failed(self, message: str) -> None:
        if self._manual:
            QMessageBox.warning(self._window, UIStrings.UPDATE_TITLE, UIStrings.UPDATE_CHECK_FAILED.format(error=message))

    def _on_update_found(self, info: UpdateInfo) -> None:
        if not self._manual and info.version == self._prefs.skipped_version:
            return
        dialog = UpdateDialog(info, self._current, self._window)
        dialog.update_requested.connect(lambda: self._start_download(info))
        dialog.skip_requested.connect(self._skip_version)
        dialog.wait_cancelled.connect(self._stop_waiting)
        dialog.page_requested.connect(lambda: self._open_page(info.page_url))
        self._dialog = dialog
        dialog.show()

    def _open_page(self, url: str) -> None:
        if update_service.is_allowed_host(url):
            self._open_url(url)

    def _skip_version(self, version: str) -> None:
        self._prefs.skipped_version = version
        update_prefs.save_preferences(self._prefs, self._prefs_path)
        if self._dialog is not None:
            self._dialog.reject()

    # --- İndirme ve kurulum ---

    def _start_download(self, info: UpdateInfo) -> None:
        if self._dialog is None:
            return
        self._dialog.show_downloading()
        worker = DownloadWorker(info, self._download_dir, self._service, parent=self)
        worker.progress.connect(self._dialog.show_downloading)
        worker.finished_ok.connect(self._on_downloaded)
        worker.failed.connect(self._on_download_failed)
        self._download_worker = worker
        worker.start()

    def _on_download_failed(self, message: str) -> None:
        if self._dialog is not None:
            self._dialog.show_error(message)

    def _on_downloaded(self, path: str) -> None:
        self._installer = Path(path)
        self._attempt = 0
        self._try_launch()

    def _try_launch(self) -> None:
        if self._installer is None or self._dialog is None:
            return
        try:
            self._service.launch_installer(self._installer, self._download_dir / "install.log")
        except InstallerBlockedError:
            self._schedule_retry()
            return
        except UpdateError as error:
            self._dialog.show_error(str(error))
            return
        self._dialog.show_installing()
        self.quit_requested.emit()

    def _schedule_retry(self) -> None:
        """Windows başlatmayı engellediyse 15 sn aralıkla en çok 40 kez yeniden dener."""
        if self._attempt >= MAX_RETRIES:
            self._stop_waiting()
            return
        self._attempt += 1
        if self._dialog is not None:
            self._dialog.show_waiting(self._attempt, MAX_RETRIES)
        QTimer.singleShot(self._retry_interval_ms, self._retry_if_waiting)

    def _retry_if_waiting(self) -> None:
        if self._installer is not None and self._attempt > 0:
            self._try_launch()

    def _stop_waiting(self) -> None:
        """Beklemeyi bırakır: dosya Gezgin'de seçili gösterilir, elle kurulum yolu açılır."""
        self._attempt = 0
        if self._dialog is not None:
            self._dialog.show_blocked()
        if self._installer is not None:
            self._reveal(self._installer)
            self._installer = None
