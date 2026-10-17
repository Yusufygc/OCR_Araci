import os
import tempfile
import unittest
from pathlib import Path

from src import selftest


class TestSelfTest(unittest.TestCase):
    def test_all_pass_returns_zero_and_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = os.path.join(tmp, "rapor.txt")
            code = selftest.run_selftest(report, checks=[("a", lambda: "tamam"), ("b", lambda: "tamam")])
            text = Path(report).read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("SONUC: BASARILI", text)
        self.assertIn("OK    a: tamam", text)

    def test_failing_check_returns_one_and_names_the_error(self):
        def broken():
            raise RuntimeError("operator torchvision::nms does not exist")

        with tempfile.TemporaryDirectory() as tmp:
            report = os.path.join(tmp, "rapor.txt")
            code = selftest.run_selftest(report, checks=[("torchvision", broken), ("diger", lambda: "tamam")])
            text = Path(report).read_text(encoding="utf-8")
        self.assertEqual(code, 1)
        self.assertIn("HATA  torchvision: RuntimeError", text)
        self.assertIn("OK    diger", text)  # bir denetimin hatası diğerlerini engellemez
        self.assertIn("SONUC: BASARISIZ", text)

    def test_real_environment_passes(self):
        """Geliştirme ortamında torchvision özel işlemleri ve motorlar gerçekten çalışmalı."""
        with tempfile.TemporaryDirectory() as tmp:
            report = os.path.join(tmp, "rapor.txt")
            code = selftest.run_selftest(report)
            text = Path(report).read_text(encoding="utf-8")
        self.assertEqual(code, 0, text)

    def test_main_exposes_selftest_flag(self):
        self.assertEqual(selftest.SELFTEST_FLAG, "--selftest")
        source = (Path(__file__).resolve().parent.parent / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn("SELFTEST_FLAG in sys.argv", source)


if __name__ == "__main__":
    unittest.main()
