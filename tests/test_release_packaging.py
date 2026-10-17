import hashlib
import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_exe
import build_installer
from src import version
from src.utils.updater import update_service

ROOT = Path(__file__).resolve().parent.parent

# Bu özetler exe'ye giren dosyalarındır (satır sonları LF'ye çevrilerek). Değişirse kararlı exe değişir:
# docs/wiki/exe_distribution.md "Exe'yi bilerek değiştirmek" adımlarını izlemeden güncelleme.
LAUNCHER_SHA256 = "7c103a99453580fabbc8ba1f405b2e860cb8b4e0f44ee722dcf2106d44e35a21"
VERSION_INFO_SHA256 = "8031b63e989d9d5050f3bbbe9ee0f4c133ba2d518149798be506a5506c7af425"
# Exe ikonu (binary, olduğu gibi) exe özetine girer; tools/make_icon.py ile yeniden üretmek özeti değiştirebilir.
ICON_SHA256 = "56fd2c93e93ee1de54177ded6a64d6e498653d10126e32c7342f6d568f2cd71c"


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_release_tool():
    spec = importlib.util.spec_from_file_location("release_tool", ROOT / "tools" / "release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestStableExeInputs(unittest.TestCase):
    def test_launcher_and_version_info_are_pinned(self):
        self.assertEqual(lf_sha256(ROOT / "packaging" / "launcher.py"), LAUNCHER_SHA256,
                         "packaging/launcher.py değişti: kararlı exe özeti değişir (docs/wiki/exe_distribution.md)")
        self.assertEqual(lf_sha256(ROOT / "packaging" / "launcher_version_info.txt"), VERSION_INFO_SHA256,
                         "launcher_version_info.txt değişti: kararlı exe özeti değişir")

    def test_exe_icon_is_pinned_and_complete(self):
        icon = ROOT / "packaging" / "app_icon.ico"
        self.assertEqual(hashlib.sha256(icon.read_bytes()).hexdigest(), ICON_SHA256,
                         "app_icon.ico değişti: kararlı exe özeti değişir (docs/wiki/exe_distribution.md)")
        from PIL import Image
        with Image.open(icon) as icon_image:
            sizes = icon_image.info["sizes"]
        for needed in ((16, 16), (32, 32), (48, 48), (256, 256)):
            self.assertIn(needed, sizes)
        window_icon = ROOT / "src" / "ui" / "assets" / "app_icon.png"
        with Image.open(window_icon) as window_image:
            self.assertEqual(window_image.size, (256, 256))

    def test_pyinstaller_arguments_keep_exe_stable(self):
        args = build_exe.pyinstaller_arguments(ROOT)
        for required in ("--onedir", "--noupx", "--debug=noarchive", "--windowed"):
            self.assertIn(required, args)
        self.assertTrue(args[0].endswith("launcher.py"))
        self.assertTrue(any(a.startswith("--version-file=") and a.endswith("launcher_version_info.txt") for a in args))
        self.assertNotIn("--onefile", args)
        self.assertTrue(any(a.startswith("--icon=") and a.endswith("app_icon.ico") for a in args))
        self.assertTrue(any(a.startswith("--add-data=") and a.endswith("src/ui/assets") for a in args))

    def test_torchvision_extension_modules_are_added_explicitly(self):
        args = build_exe.torchvision_extension_arguments()
        self.assertTrue(args, "torchvision uzantı modülleri (.pyd/.so) bulunamadı")
        self.assertTrue(all(a.startswith("--add-binary=") and a.endswith("torchvision") for a in args))
        self.assertTrue(any("_C" in a for a in args))
        for argument in args:
            self.assertIn(argument, build_exe.pyinstaller_arguments(ROOT))

    def test_build_script_fixes_epoch(self):
        source = (ROOT / "build_exe.py").read_text(encoding="utf-8")
        self.assertEqual(build_exe.LAUNCHER_EPOCH, 1700000000)
        self.assertIn('os.environ["SOURCE_DATE_EPOCH"] = str(LAUNCHER_EPOCH)', source)

    def test_build_pins_pyinstaller_and_lf_endings(self):
        requirements = (ROOT / "requirements-build.txt").read_text(encoding="utf-8")
        self.assertRegex(requirements, r"(?m)^pyinstaller==\d+\.\d+\.\d+$")
        self.assertIn("* text=auto eol=lf", (ROOT / ".gitattributes").read_text(encoding="utf-8"))

    def test_no_version_dependent_exe_resource_at_root(self):
        self.assertFalse((ROOT / "version_info.txt").exists())
        self.assertIn("1.0.0.0", (ROOT / "packaging" / "launcher_version_info.txt").read_text(encoding="utf-8"))


class TestLauncherHashGate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.exe = self.dir / "OCRAraci.exe"
        self.exe.write_bytes(b"exe-icerigi")
        self.hash_file = self.dir / "launcher.sha256"

    def test_missing_approval_stops(self):
        with self.assertRaises(SystemExit):
            build_exe.check_launcher_hash(self.exe, self.hash_file)

    def test_update_writes_then_same_hash_passes(self):
        digest = build_exe.check_launcher_hash(self.exe, self.hash_file, update=True)
        self.assertEqual(self.hash_file.read_text(encoding="ascii").split()[0], digest)
        self.assertEqual(build_exe.check_launcher_hash(self.exe, self.hash_file), digest)

    def test_different_hash_stops(self):
        build_exe.check_launcher_hash(self.exe, self.hash_file, update=True)
        self.exe.write_bytes(b"degisti")
        with self.assertRaises(SystemExit):
            build_exe.check_launcher_hash(self.exe, self.hash_file)

    def test_committed_approval_file_format_if_present(self):
        approval = ROOT / "packaging" / "launcher.sha256"
        if approval.exists():
            self.assertRegex(approval.read_text(encoding="ascii").strip(), r"^[0-9a-f]{64} \*OCRAraci\.exe$")


class TestInstallerScript(unittest.TestCase):
    def setUp(self):
        self.iss = (ROOT / "packaging" / "OCRAraci.iss").read_text(encoding="utf-8-sig")

    def test_inno_settings(self):
        self.assertIn("PrivilegesRequired=lowest", self.iss)
        self.assertIn("SetupIconFile=app_icon.ico", self.iss)
        self.assertIn("CloseApplications=yes", self.iss)
        self.assertIn("Check: RelaunchAfterUpdate", self.iss)
        self.assertIn("WizardSilent and not HasParam('/VERYSILENT')", self.iss)
        self.assertIn(f"OutputBaseFilename={version.INSTALLER_PREFIX}-Setup-", self.iss)
        self.assertIn(f'#define AppExe "{version.EXE_NAME}.exe"', self.iss)

    def test_app_id_is_fixed_and_consistent(self):
        match = re.search(r"AppId=\{\{([0-9A-F-]{36})\}", self.iss)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), build_installer.APP_ID)

    def test_no_licensing_or_signing_directives(self):
        for forbidden in ("LicenseFile", "SignTool", "SignedUninstaller"):
            self.assertNotIn(forbidden, self.iss)

    def test_installer_name_matches_updater_pattern(self):
        name = build_installer.installer_path("1.2.3").name
        self.assertRegex(name, update_service.INSTALLER_NAME_PATTERN)

    def test_checksum_file_written_next_to_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            installer = Path(tmp) / "OCRAraci-Setup-1.2.3.exe"
            installer.write_bytes(b"veri")
            checksum = build_installer.write_checksum(installer)
            self.assertEqual(checksum.name, installer.name + ".sha256")
            self.assertEqual(checksum.read_text(encoding="ascii").split()[0], hashlib.sha256(b"veri").hexdigest())


class TestReleaseWorkflowAndVersion(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    def test_workflow_gates(self):
        self.assertIn("python build_installer.py", self.workflow)
        self.assertNotIn("--no-verify", self.workflow)
        self.assertIn("--verify-tag", self.workflow)
        self.assertIn("--check-tag", self.workflow)
        self.assertIn("TAG: ${{ github.ref_name }}", self.workflow)
        self.assertIn("unittest discover tests", self.workflow)
        self.assertIn("windows-latest", self.workflow)

    def test_version_format(self):
        self.assertRegex(version.__version__, r"^\d+\.\d+\.\d+$")
        self.assertEqual(update_service.parse_version(version.__version__) is not None, True)

    def test_release_tool_version_roundtrip_and_tag_check(self):
        tool = load_release_tool()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "version.py"
            path.write_text('__version__ = "1.0.0"\nRELEASE_REPO = ""\n', encoding="utf-8")
            self.assertEqual(tool.read_version(path), "1.0.0")
            tool.write_version("1.2.3", path)
            self.assertEqual(tool.read_version(path), "1.2.3")
            self.assertIn('RELEASE_REPO = ""', path.read_text(encoding="utf-8"))
            tool.check_tag("v1.2.3", path)
            with self.assertRaises(ValueError):
                tool.check_tag("v1.2.4", path)

    def test_release_tool_rejects_bad_state(self):
        tool = load_release_tool()
        with self.assertRaises(ValueError):
            tool.parse_version("1.2")
        with patch.object(tool, "git", return_value=" M dosya.py"):
            with self.assertRaises(ValueError):
                tool.ensure_releasable("9.9.9")
        answers = {"status": "", "rev-parse": "feature/x"}
        with patch.object(tool, "git", side_effect=lambda *a: answers.get(a[0], "")):
            with self.assertRaises(ValueError):
                tool.ensure_releasable("9.9.9")
        answers["rev-parse"] = "main"
        with patch.object(tool, "git", side_effect=lambda *a: answers.get(a[0], "")):
            with self.assertRaises(ValueError):
                tool.ensure_releasable("0.0.1")  # mevcuttan küçük
            tool.ensure_releasable("9.9.9")  # geçerli
        answers["tag"] = "v9.9.9"
        with patch.object(tool, "git", side_effect=lambda *a: answers.get(a[0], "")):
            with self.assertRaises(ValueError):
                tool.ensure_releasable("9.9.9")


if __name__ == "__main__":
    unittest.main()
