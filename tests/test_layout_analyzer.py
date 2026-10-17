import unittest
from src.core.layout.xy_cut_analyzer import XYCutLayoutAnalyzer
from src.core.layout.layout_interface import RegionAnalysisResult


class TestLayoutAnalyzer(unittest.TestCase):
    """Unit tests for XYCutLayoutAnalyzer spatial block extraction and ordering."""

    def setUp(self):
        self.analyzer = XYCutLayoutAnalyzer()

    def test_empty_input(self):
        res = self.analyzer.analyze([], (100, 100))
        self.assertIsInstance(res, RegionAnalysisResult)
        self.assertEqual(len(res.blocks), 0)
        self.assertEqual(res.full_text, "")

    def test_single_box(self):
        sample_boxes = [
            {
                "text": "Başlık",
                "confidence": 0.95,
                "bbox": [[10, 10], [60, 10], [60, 30], [10, 30]]
            }
        ]
        res = self.analyzer.analyze(sample_boxes, (200, 200))
        self.assertEqual(len(res.blocks), 1)
        self.assertIn("Başlık", res.full_text)
        self.assertAlmostEqual(res.confidence, 0.95)

    def test_multi_column_separation(self):
        # Two columns on the same Y horizontal level (y: 20 to 45), separated by 60px horizontally
        sample_boxes = [
            {
                "text": "Sol Sütun",
                "confidence": 0.90,
                "bbox": [[10, 20], [80, 20], [80, 45], [10, 45]]
            },
            {
                "text": "Sağ Sütun",
                "confidence": 0.92,
                "bbox": [[150, 20], [220, 20], [220, 45], [150, 45]]
            }
        ]
        res = self.analyzer.analyze(sample_boxes, (200, 300))
        # Must be separated into 2 distinct blocks rather than a single entangled line
        self.assertEqual(len(res.blocks), 2)
        block_texts = [b.text for b in res.blocks]
        self.assertIn("Sol Sütun", block_texts)
        self.assertIn("Sağ Sütun", block_texts)

    def test_reading_order_hierarchy(self):
        # Top block, and two middle blocks
        sample_boxes = [
            {
                "text": "Alt Blok",
                "confidence": 0.88,
                "bbox": [[10, 200], [100, 200], [100, 230], [10, 230]]
            },
            {
                "text": "Üst Başlık",
                "confidence": 0.99,
                "bbox": [[10, 10], [120, 10], [120, 35], [10, 35]]
            }
        ]
        res = self.analyzer.analyze(sample_boxes, (300, 300))
        self.assertEqual(len(res.blocks), 2)
        # First block should be the top one
        self.assertEqual(res.blocks[0].text, "Üst Başlık")
        self.assertEqual(res.blocks[1].text, "Alt Blok")


if __name__ == "__main__":
    unittest.main()
