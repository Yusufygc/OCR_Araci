import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from src.core.interfaces.ocr_interface import OCRResult, IOCREngine
from src.core.factories.ocr_factory import OCREngineFactory
from src.core.engines.easyocr_engine import EasyOCREngine
from src.core.engines.tesseract_engine import TesseractEngine


class TestOCREnginesAndFactory(unittest.TestCase):
    """Unit tests for OCR engines, result models and engine factory."""

    def test_ocr_result_model(self):
        result = OCRResult(
            text="Merhaba Dünya",
            confidence=0.95,
            processing_time=0.12,
            details=[{"text": "Merhaba", "confidence": 0.95}],
            success=True,
            error_message=None
        )
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Merhaba Dünya")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.processing_time, 0.12)
        self.assertEqual(len(result.details), 1)

    def test_ocr_factory_list_engines(self):
        engines = OCREngineFactory.list_available_engines()
        self.assertIsInstance(engines, list)
        keys = [eng["id"] for eng in engines]
        self.assertIn("easyocr", keys)
        self.assertIn("tesseract", keys)

    def test_ocr_factory_get_engine_caching(self):
        engine1 = OCREngineFactory.get_engine("easyocr")
        engine2 = OCREngineFactory.get_engine("easyocr")
        self.assertIsInstance(engine1, IOCREngine)
        self.assertIsInstance(engine1, EasyOCREngine)
        self.assertIs(engine1, engine2)

        tess1 = OCREngineFactory.get_engine("tesseract")
        tess2 = OCREngineFactory.get_engine("tesseract")
        self.assertIsInstance(tess1, IOCREngine)
        self.assertIsInstance(tess1, TesseractEngine)
        self.assertIs(tess1, tess2)

    def test_ocr_factory_invalid_engine(self):
        with self.assertRaises(ValueError):
            OCREngineFactory.get_engine("non_existent_engine")

    def test_easyocr_engine_properties(self):
        engine = EasyOCREngine()
        self.assertIn("EasyOCR", engine.name)
        self.assertTrue(engine.is_available)

    def test_easyocr_engine_extract_mock(self):
        engine = EasyOCREngine()
        dummy_img = np.full((100, 100, 3), 255, dtype=np.uint8)

        mock_reader = MagicMock()
        mock_reader.readtext.return_value = [
            ([[0, 0], [10, 0], [10, 10], [0, 10]], "Test Metni", 0.92)
        ]

        with patch.object(engine, "_get_reader", return_value=mock_reader):
            res = engine.extract_text(dummy_img, lang="tur+eng")
            self.assertTrue(res.success)
            self.assertEqual(res.text, "Test Metni")
            self.assertAlmostEqual(res.confidence, 0.92)
            self.assertEqual(len(res.details), 1)

    def test_easyocr_2d_line_clustering(self):
        engine = EasyOCREngine()
        # Two boxes on line 1 (out of X order) and one box on line 2
        raw_results = [
            ([[120, 12], [200, 12], [200, 32], [120, 32]], "Dünya", 0.90),
            ([[10, 10], [100, 10], [100, 30], [10, 30]], "Merhaba", 0.96),
            ([[10, 60], [150, 60], [150, 80], [10, 80]], "Alt Satır", 0.88),
        ]
        full_text, avg_conf, details = engine._format_ocr_results(raw_results)
        self.assertEqual(full_text, "Merhaba Dünya\nAlt Satır")
        self.assertEqual(len(details), 3)
        self.assertAlmostEqual(avg_conf, (0.90 + 0.96 + 0.88) / 3.0)

    def test_tesseract_engine_properties(self):
        engine = TesseractEngine()
        self.assertIn("Tesseract", engine.name)

    def test_tesseract_extract_mock(self):
        engine = TesseractEngine()
        dummy_img = np.full((100, 100, 3), 255, dtype=np.uint8)

        mock_dict = {
            'conf': [95, 90, -1, 85],
            'text': ['Tesseract', 'Çıktısı', '   ', 'İkinciSatır'],
            'block_num': [1, 1, 1, 1],
            'par_num': [1, 1, 1, 1],
            'line_num': [1, 1, 1, 2],
            'left': [10, 65, 0, 10],
            'top': [10, 10, 0, 40],
            'width': [50, 40, 0, 80],
            'height': [20, 20, 0, 20]
        }

        with patch("pytesseract.image_to_data", return_value=mock_dict):
            res = engine.extract_text(dummy_img, lang="tur")
            self.assertTrue(res.success)
            self.assertEqual(res.text, "Tesseract Çıktısı\nİkinciSatır")
            self.assertAlmostEqual(res.confidence, (95 + 90 + 85) / 300.0)
            self.assertEqual(len(res.details), 3)

    def test_icon_noise_filtering(self):
        self.assertTrue(TesseractEngine._is_low_conf_noise("MA", 10.0))
        self.assertTrue(TesseractEngine._is_low_conf_noise("j", 50.0))
        self.assertTrue(TesseractEngine._is_low_conf_noise("$", 80.0))
        self.assertFalse(TesseractEngine._is_low_conf_noise("|", 65.0))
        self.assertFalse(TesseractEngine._is_low_conf_noise("Merhaba", 92.0))

        easy = EasyOCREngine()
        raw_results = [
            ([[0, 0], [10, 0], [10, 10], [0, 10]], "Ts", 0.05),
            ([[10, 0], [20, 0], [20, 10], [10, 10]], "@ #", 0.30),
            ([[30, 0], [100, 0], [100, 20], [30, 20]], "Temiz Metin", 0.91),
        ]
        txt, conf, det = easy._format_ocr_results(raw_results)
        self.assertEqual(txt, "Temiz Metin")
        self.assertEqual(len(det), 1)
        self.assertAlmostEqual(conf, 0.91)


class TestEngineBBoxCoordinates(unittest.TestCase):
    """OCR kutuları, ön hazırlık (2x büyütme + pad) sonrası bile orijinal görsel uzayında dönmeli."""

    def test_tesseract_details_use_original_image_space(self):
        import cv2
        engine = TesseractEngine()
        if not engine.is_available:
            self.skipTest("Tesseract yüklü değil")
        # Geniş şerit (w>=500, h<360): 2x büyütme + 16px pad uygulanır.
        img = np.full((120, 700, 3), 255, dtype=np.uint8)
        cv2.putText(img, "HELLO WORLD", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 3)
        res = engine.extract_text(img, lang="eng")
        self.assertTrue(res.success)
        self.assertTrue(res.details)
        for d in res.details:
            for x, y in d["bbox"]:
                self.assertLessEqual(x, 700 + 2)
                self.assertLessEqual(y, 120 + 2)
        self.assertLess(min(p[0] for d in res.details for p in d["bbox"]), 60)

    def test_easyocr_details_use_original_image_space(self):
        engine = EasyOCREngine(gpu=False)
        reader = MagicMock()
        # Hazırlanmış (2x + 16px pad) uzayda tek kutu: orijinalde (50,25)-(150,50)
        reader.readtext.return_value = [
            ([[116, 66], [316, 66], [316, 116], [116, 116]], "Merhaba", 0.95)
        ]
        engine._reader = reader
        engine._loaded_langs = ["tr", "en"]
        img = np.full((250, 600, 3), 255, dtype=np.uint8)
        res = engine.extract_text(img, lang="tur+eng")
        self.assertTrue(res.success)
        self.assertEqual(res.details[0]["bbox"][0], [50.0, 25.0])
        self.assertEqual(res.details[0]["bbox"][2], [150.0, 50.0])


if __name__ == "__main__":
    unittest.main()

