import unittest
import os
import numpy as np
import cv2
from src.core.processing.image_processor import ImageProcessor
from src.core.factories.ocr_factory import OCREngineFactory
from src.utils.exporters.exporter_factory import ExporterFactory


class TestOCRCore(unittest.TestCase):

    def setUp(self):
        # Create a synthetic white image with black text rectangle
        self.img = np.full((200, 400, 3), 255, dtype=np.uint8)
        cv2.putText(self.img, "TEST OCR", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

    def test_image_processor(self):
        gray = ImageProcessor.to_grayscale(self.img)
        self.assertEqual(len(gray.shape), 2)

        contrast = ImageProcessor.enhance_contrast(self.img)
        self.assertEqual(len(contrast.shape), 2)

        denoised = ImageProcessor.denoise(self.img)
        self.assertIsNotNone(denoised)

        binarized = ImageProcessor.binarize_adaptive(self.img)
        self.assertEqual(binarized.shape, gray.shape)

        cropped = ImageProcessor.crop_roi(self.img, 10, 10, 100, 50)
        self.assertEqual(cropped.shape[0], 50)
        self.assertEqual(cropped.shape[1], 100)

    def test_ocr_factory(self):
        engines = OCREngineFactory.list_available_engines()
        self.assertIsInstance(engines, list)
        self.assertTrue(len(engines) >= 2)

    def test_pdf_exporter_turkish(self):
        exporter = ExporterFactory.get_exporter("pdf")
        self.assertEqual(exporter.file_extension, ".pdf")
        
        test_pdf = "test_output_turkish.pdf"
        success = exporter.export("Türkçe Karakter Testi: ğ Ğ ş Ş ı İ ç Ç ö Ö ü Ü", test_pdf)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(test_pdf))
        
        # Cleanup test file
        if os.path.exists(test_pdf):
            os.remove(test_pdf)


if __name__ == "__main__":
    unittest.main()
