import unittest
import numpy as np
import cv2
from src.core.processing.image_processor import ImageProcessor


class TestImageProcessorPolarityAndCoordinates(unittest.TestCase):
    """Koyu zemin polaritesi (deskew, paint temizleme) ve OCR koordinat dönüşümü testleri."""

    def test_prepare_for_ocr_with_transform_and_restore_roundtrip(self):
        wide_strip = np.full((250, 600, 3), 255, dtype=np.uint8)
        prepared, scale, pad = ImageProcessor.prepare_for_ocr_with_transform(wide_strip, pad=16)
        self.assertEqual((prepared.shape, scale, pad), ((532, 1232, 3), 2.0, 16))

        # Hazırlanmış görseldeki (2x + 16px pad) kutu, orijinal görsel uzayına geri çevrilmeli.
        details = [{"text": "x", "confidence": 0.9, "bbox": [[116, 66], [316, 66], [316, 116], [116, 116]]}]
        restored = ImageProcessor.restore_details_coordinates(details, scale, pad)
        self.assertEqual(restored[0]["bbox"][0], [50.0, 25.0])
        self.assertEqual(restored[0]["bbox"][2], [150.0, 50.0])
        self.assertEqual(details[0]["bbox"][0], [116, 66])  # girdi değişmemeli

        large = np.full((200, 250, 3), 255, dtype=np.uint8)
        _, scale_l, pad_l = ImageProcessor.prepare_for_ocr_with_transform(large)
        self.assertEqual((scale_l, pad_l), (1.0, 0))
        self.assertIs(ImageProcessor.restore_details_coordinates(details, scale_l, pad_l), details)

    def test_shift_details_coordinates(self):
        details = [{"text": "x", "bbox": [[1, 2], [3, 2], [3, 4], [1, 4]]}]
        shifted = ImageProcessor.shift_details_coordinates(details, 10, 20)
        self.assertEqual(shifted[0]["bbox"][0], [11, 22])
        self.assertEqual(details[0]["bbox"][0], [1, 2])
        self.assertIs(ImageProcessor.shift_details_coordinates(details, 0, 0), details)

    @staticmethod
    def _text_lines_canvas(dark: bool) -> np.ndarray:
        bg, fg = ((20, 20, 20), (235, 235, 235)) if dark else ((255, 255, 255), (20, 20, 20))
        canvas = np.full((300, 600, 3), bg, dtype=np.uint8)
        for row, y in enumerate(range(60, 260, 50)):
            for col in range(8):
                x = 40 + col * 65
                cv2.rectangle(canvas, (x, y), (x + 50, y + 12), fg, -1)
        return canvas

    def test_deskew_dark_unskewed_image_stays_unrotated(self):
        # Koyu zeminde düz metin yanlış eğim (ör. -14°) üretmemeli; görsel aynen dönmeli.
        dark = self._text_lines_canvas(dark=True)
        gray = ImageProcessor.to_grayscale(dark)
        self.assertLess(abs(ImageProcessor._estimate_skew_angle(gray)), 0.3)
        np.testing.assert_array_equal(ImageProcessor.deskew(dark), dark)

    def test_deskew_dark_skewed_image_detects_angle_and_uses_background_border(self):
        dark = self._text_lines_canvas(dark=True)
        rot = cv2.getRotationMatrix2D((300, 150), -5.0, 1.0)
        skewed = cv2.warpAffine(dark, rot, (600, 300), borderValue=(20, 20, 20))
        angle = ImageProcessor._estimate_skew_angle(ImageProcessor.to_grayscale(skewed))
        self.assertGreater(abs(angle), 2.0)

        fixed = ImageProcessor.deskew(skewed)
        self.assertEqual(fixed.shape, skewed.shape)
        # Kenar boşluğu beyaz değil, koyu zemin rengiyle dolmalı.
        self.assertLess(int(fixed[0, 0, 0]), 60)
        self.assertLess(int(fixed[-1, -1, 0]), 60)

    def test_remove_color_annotations_dark_background_keeps_background_tone(self):
        canvas = np.full((120, 300, 3), 20, dtype=np.uint8)
        cv2.line(canvas, (10, 60), (280, 60), (0, 0, 255), 12)
        cleaned = ImageProcessor.remove_color_annotations(canvas)
        # Kalın çizgi çekirdeği beyaza değil koyu zemine boyanmalı.
        self.assertLess(int(cleaned[60, 150]), 80)


if __name__ == "__main__":
    unittest.main()
