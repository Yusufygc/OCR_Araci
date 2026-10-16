import unittest
import numpy as np
import cv2
from src.core.processing.image_processor import ImageProcessor
from src.core.factories.ocr_factory import OCREngineFactory


class TestEndToEndOCR(unittest.TestCase):

    def test_full_pipeline(self):
        # 1. Create a clean sample image with text
        img = np.full((300, 600, 3), 255, dtype=np.uint8)
        cv2.putText(img, "TEST OCR", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

        # 2. Add red drawing noise on top of text (simulating user's drawn-on images)
        cv2.line(img, (20, 20), (580, 280), (0, 0, 255), 4)

        # 3. Apply color mask preprocessing to remove red line
        clean_img = ImageProcessor.remove_color_annotations(img)

        # 4. Extract text using EasyOCR engine
        engine = OCREngineFactory.get_engine("easyocr")
        result = engine.extract_text(clean_img, lang="tur+eng")

        if not result.success:
            print("OCR Error Message:", result.error_message)

        self.assertTrue(result.success, msg=f"OCR Failed: {result.error_message}")
        print(f"Extracted Text: '{result.text}' (Confidence: {result.confidence:.2f})")


if __name__ == "__main__":
    unittest.main()
