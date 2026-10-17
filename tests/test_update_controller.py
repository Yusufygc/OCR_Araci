import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMainWindow

from src.ui.update_controller import UpdateController, UpdateSettings
from src.utils.updater.update_service import InstallerBlockedError, UpdateError, UpdateInfo

INFO = UpdateInfo(
    version="1.2.0", tag="v1.2.0", installer_name="OCRAraci-Setup-1.2.0.exe",
    download_url="https://github.com/a/b/releases/download/v1.2.0/OCRAraci-Setup-1.2.0.exe",
    size=10, sha256="0" * 64, checksum_url=None, notes="Notlar", page_url="https://github.com/a/b/releases/tag/v1.2.0",
)


class FakeService:
    def __init__(self, info=INFO, check_error=None, blocked_times=0, launch_error=None):
        self.info, self.check_error = info, check_error
        self.blocked_times, self.launch_error = blocked_times, launch_error
        self.launch_calls = 0
        self.download_dir = None

    def check_for_update(self, current, repo):
        if self.check_error:
            raise self.check_error
        return self.info

    def download_installer(self, info, dest_dir, progress=None):
        self.download_dir = dest_dir
        if progress:
            progress(5, 10)
            progress(10, 10)
        return Path(dest_dir) / info.installer_name

    def launch_installer(self, installer, log_path=None):
        self.launch_calls += 1
        if self.launch_error:
            raise self.launch_error
        if self.launch_calls <= self.blocked_times:
            raise InstallerBlockedError("engel")


class TestUpdateController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.window = QMainWindow()
        self.revealed, self.opened, self.quit_calls = [], [], []

    def _controller(self, service, repo="a/b", current="1.0.0", retry_ms=10):
        settings = UpdateSettings(
            repo=repo, current_version=current, prefs_path=self.tmp / "updates.json",
            download_dir=self.tmp / "dl", retry_interval_ms=retry_ms,
            reveal=self.revealed.append, open_url=self.opened.append,
        )
        controller = UpdateController(self.window, service=service, settings=settings)
        controller.quit_requested.connect(lambda: self.quit_calls.append(1))
        return controller

    def _wait(self, condition, timeout_ms=3000):
        waited = 0
        while not condition() and waited < timeout_ms:
            self.app.processEvents()
            self.app.thread().msleep(10)
            waited += 10
        self.app.processEvents()
        self.assertTrue(condition(), "zaman aşımı")

    def _start(self, controller, manual=True):
        controller.check(manual=manual)
        self._wait(lambda: controller._dialog is not None)
        return controller._dialog

    def test_update_found_download_and_install_quits_app(self):
        service = FakeService()
        controller = self._controller(service)
        dialog = self._start(controller)
        self.assertIn("1.2.0", dialog.lbl_title.text())
        dialog.btn_update.click()
        self._wait(lambda: bool(self.quit_calls))
        self.assertEqual(service.launch_calls, 1)
        self.assertEqual(service.download_dir, self.tmp / "dl")

    def test_blocked_installer_retries_then_succeeds(self):
        service = FakeService(blocked_times=2)
        controller = self._controller(service, retry_ms=10)
        dialog = self._start(controller)
        dialog.btn_update.click()
        self._wait(lambda: bool(self.quit_calls))
        self.assertEqual(service.launch_calls, 3)

    def test_wait_cancel_reveals_installer_and_shows_page_button(self):
        service = FakeService(blocked_times=999)
        controller = self._controller(service, retry_ms=50)
        dialog = self._start(controller)
        dialog.btn_update.click()
        self._wait(lambda: dialog.btn_stop_wait.isVisibleTo(dialog))
        dialog.btn_stop_wait.click()
        self.assertEqual(len(self.revealed), 1)
        self.assertTrue(dialog.btn_page.isVisibleTo(dialog))
        dialog.btn_page.click()
        self.assertEqual(self.opened, [INFO.page_url])
        self.assertEqual(self.quit_calls, [])

    def test_launch_error_shows_error_without_quitting(self):
        service = FakeService(launch_error=UpdateError("kurulamadi"))
        controller = self._controller(service)
        dialog = self._start(controller)
        dialog.btn_update.click()
        self._wait(lambda: "kurulamadi" in dialog.lbl_status.text())
        self.assertEqual(self.quit_calls, [])

    def test_skip_version_persists_and_silences_startup_check(self):
        service = FakeService()
        controller = self._controller(service)
        dialog = self._start(controller)
        dialog.btn_skip.click()
        self.assertEqual(controller._prefs.skipped_version, "1.2.0")

        again = self._controller(service)
        again.check(manual=False)
        self._wait(lambda: again._check_worker is not None and again._check_worker.isFinished())
        self.assertIsNone(again._dialog)

    def test_no_repo_never_checks_and_manual_check_informs(self):
        service = FakeService()
        controller = self._controller(service, repo="")
        with patch("src.ui.update_controller.QMessageBox.information") as info_box:
            controller.check(manual=False)
            info_box.assert_not_called()
            controller.check(manual=True)
            info_box.assert_called_once()
        self.assertIsNone(controller._check_worker)

    def test_silent_failure_on_startup_but_manual_warns(self):
        service = FakeService(check_error=UpdateError("ag yok"))
        controller = self._controller(service)
        with patch("src.ui.update_controller.QMessageBox.warning") as warn_box:
            controller.check(manual=False)
            self._wait(lambda: controller._check_worker.isFinished())
            warn_box.assert_not_called()
            controller.check(manual=True)
            self._wait(lambda: warn_box.called)

    def test_up_to_date_message_only_when_manual(self):
        service = FakeService(info=None)
        controller = self._controller(service)
        with patch("src.ui.update_controller.QMessageBox.information") as info_box:
            controller.check(manual=False)
            self._wait(lambda: controller._check_worker.isFinished())
            info_box.assert_not_called()
            controller.check(manual=True)
            self._wait(lambda: info_box.called)

    def test_page_button_ignores_disallowed_host(self):
        controller = self._controller(FakeService())
        controller._open_page("https://evil.example.com/x")
        controller._open_page("https://github.com/a/b")
        self.assertEqual(self.opened, ["https://github.com/a/b"])

    def test_menu_has_version_check_and_auto_toggle(self):
        controller = self._controller(FakeService())
        controller.install_menu(self.window.menuBar())
        texts = [a.text() for a in self.window.menuBar().actions()[0].menu().actions()]
        self.assertEqual(len(texts), 3)
        self.assertIn("1.0.0", texts[0])
        controller.act_auto.setChecked(False)
        self.assertFalse(controller._prefs.check_on_startup)
        self.assertFalse(__import__("json").loads((self.tmp / "updates.json").read_text(encoding="utf-8"))["check_on_startup"])


if __name__ == "__main__":
    unittest.main()
