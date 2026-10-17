import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_verify


class TestInstallerCheckIsolation(unittest.TestCase):
    """Deneme kurulumu çökse bile gerçek kurulumun kaydı geri yazılmalı; geçici klasör silinmeli."""

    def _run_check(self, install_error=None, launch_alive=True):
        events = []
        created = []

        def fake_install(installer, target):
            created.append(target)
            events.append("install")
            target.with_name(target.name + ".log").write_text("kurulum günlüğü", encoding="utf-8")
            if install_error:
                raise install_error

        with patch.object(build_verify, "_silent_install", fake_install), \
                patch.object(build_verify, "_silent_uninstall", lambda target: events.append("uninstall")), \
                patch.object(build_verify, "launch_check", lambda exe, **kw: launch_alive):
            try:
                spec = build_verify.InstallerCheckSpec(
                    "APP-ID", "App.exe", [],
                    save=lambda app_id, shortcuts: events.append("save") or {"app_id": app_id},
                    restore=lambda snapshot: events.append("restore"),
                )
                build_verify.installer_check(Path("setup.exe"), spec)
            except Exception as error:  # testin kendisi sonucu inceler
                events.append(type(error).__name__)
        return events, created

    def test_success_saves_installs_uninstalls_restores(self):
        events, created = self._run_check()
        self.assertEqual(events, ["save", "install", "uninstall", "restore"])
        self.assertFalse(created[0].exists())
        self.assertFalse(created[0].with_name(created[0].name + ".log").exists())

    def test_install_failure_still_restores(self):
        events, created = self._run_check(install_error=RuntimeError("kurulum cokti"))
        self.assertEqual(events, ["save", "install", "restore", "RuntimeError"])
        self.assertFalse(created[0].exists())

    def test_exe_exits_immediately_still_restores(self):
        events, _ = self._run_check(launch_alive=False)
        self.assertEqual(events, ["save", "install", "restore", "RuntimeError"])


class TestLaunchCheck(unittest.TestCase):
    def test_sac_block_raises_launch_blocked(self):
        error = OSError("engel")
        error.winerror = 4551
        with patch.object(build_verify.subprocess, "Popen", side_effect=error):
            with self.assertRaises(build_verify.LaunchBlockedError):
                build_verify.launch_check(Path("x.exe"), seconds=0)

    def test_other_os_error_propagates(self):
        with patch.object(build_verify.subprocess, "Popen", side_effect=OSError("baska")):
            with self.assertRaises(OSError):
                build_verify.launch_check(Path("x.exe"), seconds=0)

    def test_alive_process_returns_true_and_exited_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "uyu.py"
            script.write_text("import time; time.sleep(30)", encoding="utf-8")
            sleeper = subprocess.Popen([sys.executable, str(script)])
            self.addCleanup(sleeper.kill)
            with patch.object(build_verify.subprocess, "Popen", return_value=sleeper), \
                    patch.object(build_verify.subprocess, "run") as killer:
                self.assertTrue(build_verify.launch_check(Path("x.exe"), seconds=0))
                killer.assert_called_once()

            done = subprocess.Popen([sys.executable, "-c", "pass"])
            done.wait()
            with patch.object(build_verify.subprocess, "Popen", return_value=done):
                self.assertFalse(build_verify.launch_check(Path("x.exe"), seconds=0))

    def test_shortcut_restore_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "alt" / "App.lnk"
            build_verify._restore_shortcut(link, b"eski")
            self.assertEqual(link.read_bytes(), b"eski")
            build_verify._restore_shortcut(link, None)
            self.assertFalse(link.exists())


if __name__ == "__main__":
    unittest.main()
