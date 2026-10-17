import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from src.utils.updater import update_service as svc
from src.utils.updater.update_service import InstallerBlockedError, UpdateError, UpdateInfo

REPO = "sahip/depo"
BASE = f"https://github.com/{REPO}/releases/download/v1.2.0"
PAYLOAD = b"kurulum-dosyasi-icerigi" * 100
PAYLOAD_SHA = hashlib.sha256(PAYLOAD).hexdigest()


class FakeResponse:
    def __init__(self, data: bytes, url: str = ""):
        self._buffer = io.BytesIO(data)
        self._url = url

    def read(self, size=-1):
        return self._buffer.read(size)

    def geturl(self):
        return self._url


def make_release(tag="v1.2.0", name="KusursuzOCR-Setup-1.2.0.exe", with_checksum=True, digest=None, **extra):
    assets = [{
        "name": name, "size": len(PAYLOAD), "browser_download_url": f"{BASE}/{name}",
        **({"digest": digest} if digest else {}),
    }]
    if with_checksum:
        assets.append({"name": f"{name}.sha256", "size": 90, "browser_download_url": f"{BASE}/{name}.sha256"})
    return {"tag_name": tag, "draft": False, "prerelease": False, "body": "Notlar",
            "html_url": f"https://github.com/{REPO}/releases/tag/{tag}", "assets": assets, **extra}


def make_info(**overrides) -> UpdateInfo:
    fields = dict(
        version="1.2.0", tag="v1.2.0", installer_name="KusursuzOCR-Setup-1.2.0.exe",
        download_url=f"{BASE}/KusursuzOCR-Setup-1.2.0.exe", size=len(PAYLOAD), sha256=PAYLOAD_SHA,
        checksum_url=None, notes="", page_url=f"https://github.com/{REPO}/releases/tag/v1.2.0",
    )
    fields.update(overrides)
    return UpdateInfo(**fields)


class TestVersionAndRelease(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(svc.parse_version("v2.10.0"), (2, 10, 0))
        self.assertGreater(svc.parse_version("2.10.0"), svc.parse_version("2.9.0"))
        self.assertIsNone(svc.parse_version("2.2.0-rc1"))
        self.assertIsNone(svc.parse_version("abc"))

    def test_newer_release_returns_info(self):
        info = svc.release_to_update(make_release(), "1.0.0", REPO)
        self.assertEqual(info.version, "1.2.0")
        self.assertEqual(info.installer_name, "KusursuzOCR-Setup-1.2.0.exe")
        self.assertTrue(info.checksum_url.endswith(".sha256"))

    def test_same_or_older_release_is_ignored(self):
        self.assertIsNone(svc.release_to_update(make_release(), "1.2.0", REPO))
        self.assertIsNone(svc.release_to_update(make_release(), "1.3.0", REPO))

    def test_prerelease_draft_and_bad_tag_ignored(self):
        self.assertIsNone(svc.release_to_update(make_release(prerelease=True), "1.0.0", REPO))
        self.assertIsNone(svc.release_to_update(make_release(draft=True), "1.0.0", REPO))
        self.assertIsNone(svc.release_to_update(make_release(tag="v1.2.0-rc1"), "1.0.0", REPO))

    def test_wrong_asset_name_or_host_rejected(self):
        self.assertIsNone(svc.release_to_update(make_release(name="Baska-Setup-1.2.0.exe"), "1.0.0", REPO))
        evil = make_release()
        evil["assets"][0]["browser_download_url"] = "https://evil.example.com/KusursuzOCR-Setup-1.2.0.exe"
        self.assertIsNone(svc.release_to_update(evil, "1.0.0", REPO))
        other_repo = make_release()
        other_repo["assets"][0]["browser_download_url"] = "https://github.com/baska/depo/releases/download/v1.2.0/KusursuzOCR-Setup-1.2.0.exe"
        self.assertIsNone(svc.release_to_update(other_repo, "1.0.0", REPO))

    def test_digest_field_is_used(self):
        info = svc.release_to_update(make_release(digest=f"sha256:{PAYLOAD_SHA}"), "1.0.0", REPO)
        self.assertEqual(info.sha256, PAYLOAD_SHA)

    def test_allowed_hosts(self):
        self.assertTrue(svc.is_allowed_host("https://github.com/a/b"))
        self.assertTrue(svc.is_allowed_host("https://objects.githubusercontent.com/x"))
        self.assertFalse(svc.is_allowed_host("http://github.com/a/b"))
        self.assertFalse(svc.is_allowed_host("https://github.com.evil.com/a"))
        self.assertFalse(svc.is_allowed_host("https://evilgithubusercontent.com/a"))


class TestFetchAndCheck(unittest.TestCase):
    def test_check_for_update_with_fake_opener(self):
        body = json.dumps(make_release()).encode()
        seen = {}

        def opener(request, timeout=None):
            seen["url"] = request.full_url
            seen["auth"] = request.get_header("Authorization")
            return FakeResponse(body)

        info = svc.check_for_update("1.0.0", REPO, opener)
        self.assertEqual(info.version, "1.2.0")
        self.assertEqual(seen["url"], f"https://api.github.com/repos/{REPO}/releases/latest")
        self.assertIsNone(seen["auth"])

    def test_invalid_repo_and_network_errors(self):
        with self.assertRaises(UpdateError):
            svc.fetch_latest_release("", lambda *a, **k: None)
        with self.assertRaises(UpdateError):
            svc.fetch_latest_release("../kotu", lambda *a, **k: None)

        def failing(request, timeout=None):
            raise OSError("ag yok")

        with self.assertRaises(UpdateError):
            svc.fetch_latest_release(REPO, failing)

    def test_oversized_or_invalid_json_rejected(self):
        with self.assertRaises(UpdateError):
            svc.fetch_latest_release(REPO, lambda r, timeout=None: FakeResponse(b"x" * (svc.MAX_API_BYTES + 5)))
        with self.assertRaises(UpdateError):
            svc.fetch_latest_release(REPO, lambda r, timeout=None: FakeResponse(b"{bozuk"))
        with self.assertRaises(UpdateError):
            svc.fetch_latest_release(REPO, lambda r, timeout=None: FakeResponse(b"[1,2]"))


class TestResolveSha256(unittest.TestCase):
    def test_prefers_digest(self):
        self.assertEqual(svc.resolve_sha256(make_info()), PAYLOAD_SHA)

    def test_reads_checksum_file(self):
        url = f"{BASE}/KusursuzOCR-Setup-1.2.0.exe.sha256"
        info = make_info(sha256=None, checksum_url=url)
        opener = lambda r, timeout=None: FakeResponse(f"{PAYLOAD_SHA.upper()} *KusursuzOCR-Setup-1.2.0.exe\n".encode(), url)
        self.assertEqual(svc.resolve_sha256(info, opener), PAYLOAD_SHA)

    def test_missing_digest_rejects_update(self):
        with self.assertRaises(UpdateError):
            svc.resolve_sha256(make_info(sha256=None, checksum_url=None))

    def test_checksum_redirect_to_bad_host_rejected(self):
        info = make_info(sha256=None, checksum_url=f"{BASE}/x.sha256")
        opener = lambda r, timeout=None: FakeResponse(PAYLOAD_SHA.encode(), "https://evil.example.com/x")
        with self.assertRaises(UpdateError):
            svc.resolve_sha256(info, opener)


class TestDownload(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dest = Path(self._tmp.name)

    def _opener(self, data=PAYLOAD, url=None):
        return lambda r, timeout=None: FakeResponse(data, url or r.full_url)

    def test_download_success_and_progress(self):
        calls = []
        path = svc.download_installer(make_info(), self.dest, lambda d, t: calls.append((d, t)), self._opener())
        self.assertEqual(path.read_bytes(), PAYLOAD)
        self.assertEqual(calls[-1], (len(PAYLOAD), len(PAYLOAD)))
        self.assertFalse(list(self.dest.glob("*.part")))

    def test_sha_mismatch_deletes_file(self):
        with self.assertRaises(UpdateError):
            svc.download_installer(make_info(sha256="0" * 64), self.dest, opener=self._opener())
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_size_mismatch_rejected(self):
        with self.assertRaises(UpdateError):
            svc.download_installer(make_info(size=len(PAYLOAD) + 1), self.dest, opener=self._opener())
        with self.assertRaises(UpdateError):
            svc.download_installer(make_info(size=len(PAYLOAD) - 1), self.dest, opener=self._opener())
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_bad_name_host_and_size_limit_rejected(self):
        for bad in (
            make_info(installer_name="..\\Evil.exe"),
            make_info(installer_name="Evil.exe"),
            make_info(download_url="https://evil.example.com/KusursuzOCR-Setup-1.2.0.exe"),
            make_info(size=svc.MAX_INSTALLER_BYTES + 1),
            make_info(size=0),
        ):
            with self.assertRaises(UpdateError):
                svc.download_installer(bad, self.dest, opener=self._opener())

    def test_redirect_to_bad_host_rejected(self):
        with self.assertRaises(UpdateError):
            svc.download_installer(make_info(), self.dest, opener=self._opener(url="https://evil.example.com/a"))


class TestLaunchInstaller(unittest.TestCase):
    NAME = Path("KusursuzOCR-Setup-1.2.0.exe")

    def test_arguments_and_flags(self):
        captured = {}

        def spawn(command, **kwargs):
            captured["command"], captured["kwargs"] = command, kwargs

        svc.launch_installer(self.NAME, Path("install.log"), spawn=spawn)
        self.assertEqual(captured["command"][0], str(self.NAME))
        self.assertIn("/SILENT", captured["command"])
        self.assertIn("/CLOSEAPPLICATIONS", captured["command"])
        self.assertTrue(any(arg.startswith("/LOG=") for arg in captured["command"]))
        self.assertNotIn("shell", captured["kwargs"])

    def test_sac_block_falls_back_to_shell_then_raises(self):
        def blocked(command, **kwargs):
            error = OSError("blok")
            error.winerror = 4551
            raise error

        ran = []
        svc.launch_installer(self.NAME, spawn=blocked, shell_execute=lambda path, params: ran.append(path) or 42)
        self.assertEqual(ran, [str(self.NAME)])

        with self.assertRaises(InstallerBlockedError):
            svc.launch_installer(self.NAME, spawn=blocked, shell_execute=lambda path, params: 5)

    def test_other_os_error_is_update_error_and_bad_name_rejected(self):
        def broken(command, **kwargs):
            raise OSError("baska hata")

        with self.assertRaises(UpdateError):
            svc.launch_installer(self.NAME, spawn=broken)
        with self.assertRaises(UpdateError):
            svc.launch_installer(Path("Kotu.exe"), spawn=lambda *a, **k: None)


if __name__ == "__main__":
    unittest.main()
