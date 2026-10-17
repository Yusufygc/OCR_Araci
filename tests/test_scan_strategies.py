import unittest
import numpy as np
from src.core.interfaces.ocr_interface import IOCREngine, OCRResult
from src.core.strategies.scan_factory import ScanStrategyFactory
from src.core.strategies.line_scan_strategy import LineScanStrategy
from src.core.strategies.block_scan_strategy import BlockScanStrategy
from src.core.strategies.multi_region_strategy import MultiRegionStrategy


class MockOCREngine(IOCREngine):
    @property
    def name(self) -> str:
        return "MockEngine"

    @property
    def is_available(self) -> bool:
        return True

    def extract_text(self, image, lang="tur+eng", **kwargs) -> OCRResult:
        details = [
            {
                "text": "Sol Kutu",
                "confidence": 0.95,
                "bbox": [[10, 10], [50, 10], [50, 30], [10, 30]]
            },
            {
                "text": "Sağ Kutu",
                "confidence": 0.90,
                "bbox": [[120, 10], [160, 10], [160, 30], [120, 30]]
            }
        ]
        return OCRResult(
            text="Sol Kutu Sağ Kutu",
            confidence=0.925,
            processing_time=0.05,
            details=details,
            success=True
        )


class TestScanStrategies(unittest.TestCase):
    """Unit tests for pluggable OCR scanning strategies and factory."""

    def setUp(self):
        self.mock_engine = MockOCREngine()
        self.dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)

    def test_factory_registry_and_modes(self):
        modes = ScanStrategyFactory.list_strategies()
        mode_ids = [m["id"] for m in modes]
        self.assertIn("line", mode_ids)
        self.assertIn("block", mode_ids)
        self.assertIn("multi_region", mode_ids)

        line_strat = ScanStrategyFactory.get_strategy("line")
        self.assertIsInstance(line_strat, LineScanStrategy)

        block_strat = ScanStrategyFactory.get_strategy("block")
        self.assertIsInstance(block_strat, BlockScanStrategy)

        fallback = ScanStrategyFactory.get_strategy("non_existent")
        self.assertIsInstance(fallback, LineScanStrategy)

    def test_line_scan_strategy(self):
        strategy = LineScanStrategy()
        self.assertEqual(strategy.mode_id, "line")
        res = strategy.execute(self.dummy_img, self.mock_engine)
        self.assertTrue(res.success)
        self.assertEqual(res.text, "Sol Kutu Sağ Kutu")

    def test_block_scan_strategy(self):
        strategy = BlockScanStrategy()
        self.assertEqual(strategy.mode_id, "block")
        res = strategy.execute(self.dummy_img, self.mock_engine)
        self.assertTrue(res.success)
        # Should split the columns into [1. Bölge] and [2. Bölge]
        self.assertIn("[1. Bölge]", res.text)
        self.assertIn("[2. Bölge]", res.text)
        self.assertIn("Sol Kutu", res.text)
        self.assertIn("Sağ Kutu", res.text)

    def test_multi_region_strategy(self):
        strategy = MultiRegionStrategy(regions=[(0, 0, 80, 50), (100, 0, 80, 50)])
        self.assertEqual(strategy.mode_id, "multi_region")
        res = strategy.execute(self.dummy_img, self.mock_engine)
        self.assertTrue(res.success)
        self.assertIn("[1. Seçili Bölge]", res.text)
        self.assertIn("[2. Seçili Bölge]", res.text)


if __name__ == "__main__":
    unittest.main()
