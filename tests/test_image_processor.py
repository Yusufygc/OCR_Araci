import unittest
import numpy as np
import cv2
from PIL import Image
from src.core.processing.image_processor import ImageProcessor


class TestImageProcessorUnit(unittest.TestCase):
    """Detailed unit tests for ImageProcessor computer vision algorithms."""

    def setUp(self):
        # Create a synthetic test image with varying pixel intensities
        self.bgr_img = np.zeros((100, 150, 3), dtype=np.uint8)
        self.bgr_img[:50, :75] = [255, 0, 0]    # Blue box
        self.bgr_img[50:, 75:] = [0, 0, 255]    # Red box
        self.bgr_img[20:40, 20:60] = [255, 255, 255] # White text box

    def test_load_image_from_numpy(self):
        loaded = ImageProcessor.load_image(self.bgr_img)
        self.assertIsInstance(loaded, np.ndarray)
        self.assertEqual(loaded.shape, self.bgr_img.shape)

    def test_load_image_from_pil(self):
        pil_img = Image.fromarray(cv2.cvtColor(self.bgr_img, cv2.COLOR_BGR2RGB))
        loaded = ImageProcessor.load_image(pil_img)
        self.assertIsInstance(loaded, np.ndarray)
        self.assertEqual(loaded.shape, self.bgr_img.shape)

    def test_load_image_invalid_type(self):
        with self.assertRaises((ValueError, TypeError)):
            ImageProcessor.load_image(12345)

    def test_to_grayscale(self):
        gray = ImageProcessor.to_grayscale(self.bgr_img)
        self.assertEqual(len(gray.shape), 2)
        self.assertEqual(gray.shape, (100, 150))

        # Check idempotency if already grayscale
        gray_again = ImageProcessor.to_grayscale(gray)
        self.assertEqual(len(gray_again.shape), 2)
        np.testing.assert_array_equal(gray, gray_again)

    def test_enhance_contrast(self):
        enhanced = ImageProcessor.enhance_contrast(self.bgr_img)
        self.assertEqual(len(enhanced.shape), 2)
        self.assertEqual(enhanced.shape, (100, 150))

    def test_denoise(self):
        denoised = ImageProcessor.denoise(self.bgr_img)
        self.assertEqual(denoised.shape[:2], self.bgr_img.shape[:2])

        gray = ImageProcessor.to_grayscale(self.bgr_img)
        denoised_gray = ImageProcessor.denoise(gray)
        self.assertEqual(denoised_gray.shape, gray.shape)

    def test_binarize_adaptive(self):
        binarized = ImageProcessor.binarize_adaptive(self.bgr_img)
        self.assertEqual(len(binarized.shape), 2)
        # Binarized should only contain 0 and 255
        unique_vals = np.unique(binarized)
        for val in unique_vals:
            self.assertIn(val, [0, 255])

    def test_remove_color_annotations(self):
        cleaned = ImageProcessor.remove_color_annotations(self.bgr_img)
        self.assertIsNotNone(cleaned)
        self.assertEqual(cleaned.shape[:2], self.bgr_img.shape[:2])
        # Red and blue saturated boxes should be filled with the background tone (dark synthetic canvas)
        bg = int(ImageProcessor.get_background_color(ImageProcessor.to_grayscale(self.bgr_img)))
        self.assertEqual(cleaned[10, 10], bg)
        self.assertEqual(cleaned[80, 120], bg)

        # Already grayscale input should return as-is
        gray_in = ImageProcessor.to_grayscale(self.bgr_img)
        gray_out = ImageProcessor.remove_color_annotations(gray_in)
        np.testing.assert_array_equal(gray_in, gray_out)

        #Selective red/blue flags
        only_red = ImageProcessor.remove_color_annotations(self.bgr_img, remove_red=True, remove_blue=False)
        self.assertEqual(only_red[80, 120], bg)

    def test_sharpen_and_padding(self):
        sharpened = ImageProcessor.sharpen(self.bgr_img)
        self.assertEqual(sharpened.shape, self.bgr_img.shape)

        padded = ImageProcessor.add_border_padding(self.bgr_img, pad=10)
        self.assertEqual(padded.shape, (120, 170, 3))

        no_pad = ImageProcessor.add_border_padding(self.bgr_img, pad=0)
        self.assertEqual(no_pad.shape, self.bgr_img.shape)

        gray = ImageProcessor.to_grayscale(self.bgr_img)
        padded_gray = ImageProcessor.add_border_padding(gray, pad=5)
        self.assertEqual(padded_gray.shape, (110, 160))

    def test_prepare_for_ocr_upscales_small_image(self):
        # 100x150 is smaller than 160 threshold, so it should upscale 2x (200x300) + 16px pad on each side -> (232, 332, 3)
        prepared = ImageProcessor.prepare_for_ocr(self.bgr_img, pad=16)
        self.assertEqual(prepared.shape, (232, 332, 3))

        # Large image >= 160x160 should preserve original dimensions without adding distortion padding
        large_img = np.full((200, 250, 3), 255, dtype=np.uint8)
        prepared_large = ImageProcessor.prepare_for_ocr(large_img, pad=10)
        self.assertEqual(prepared_large.shape, (200, 250, 3))

    def test_binarize_adaptive_even_custom_block(self):
        binarized = ImageProcessor.binarize_adaptive(self.bgr_img, block_size=12, c=4)
        self.assertEqual(binarized.shape, (100, 150))

    def test_deskew(self):
        # Create synthetic image with tilted horizontal black line on white background
        canvas = np.full((200, 400, 3), 255, dtype=np.uint8)
        cv2.line(canvas, (30, 80), (370, 110), (0, 0, 0), 4)
        cv2.line(canvas, (30, 120), (370, 150), (0, 0, 0), 4)
        deskewed = ImageProcessor.deskew(canvas)
        self.assertEqual(deskewed.shape[:2], canvas.shape[:2])

        # Blank canvas with no lines returns 0.0 skew and original image
        blank = np.full((100, 100), 255, dtype=np.uint8)
        self.assertEqual(ImageProcessor._estimate_skew_angle(blank), 0.0)
        np.testing.assert_array_equal(ImageProcessor.deskew(blank), blank)

    def test_crop_roi(self):
        cropped = ImageProcessor.crop_roi(self.bgr_img, 10, 15, 60, 40)
        self.assertEqual(cropped.shape, (40, 60, 3))

    def test_load_image_oversized_dimension(self):
        # Image exceeding 8000 px should raise ValueError
        huge_img = np.zeros((8005, 10, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            ImageProcessor.load_image(huge_img)

    def test_dark_polarity_and_background_color(self):
        dark_img = np.zeros((50, 50, 3), dtype=np.uint8)
        self.assertTrue(ImageProcessor.is_dark_image(dark_img))
        inverted = ImageProcessor.invert_if_dark(dark_img)
        self.assertEqual(int(inverted[0, 0, 0]), 255)

        light_img = np.full((50, 50, 3), 255, dtype=np.uint8)
        self.assertFalse(ImageProcessor.is_dark_image(light_img))
        same = ImageProcessor.invert_if_dark(light_img)
        np.testing.assert_array_equal(light_img, same)

        bg = ImageProcessor.get_background_color(light_img)
        self.assertEqual(bg, (255, 255, 255))

    def test_prepare_for_ocr_wide_strip(self):
        wide_strip = np.full((250, 600, 3), 255, dtype=np.uint8)
        prepared = ImageProcessor.prepare_for_ocr(wide_strip, pad=16)
        self.assertEqual(prepared.shape, (532, 1232, 3))

    def test_remove_color_annotations_paint_scribbles(self):
        canvas = np.full((120, 300, 3), 255, dtype=np.uint8)
        cv2.line(canvas, (60, 20), (60, 100), (20, 20, 20), 4)
        cv2.line(canvas, (10, 60), (280, 60), (0, 0, 255), 2)
        cv2.rectangle(canvas, (15, 25), (270, 95), (255, 50, 0), 2)
        cleaned = ImageProcessor.remove_color_annotations(canvas)
        self.assertEqual(cleaned.shape, (120, 300))
        self.assertGreater(int(cleaned[60, 150]), 240)
        self.assertLess(int(cleaned[40, 60]), 50)


if __name__ == "__main__":
    unittest.main()

