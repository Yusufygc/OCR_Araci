import os
import cv2
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_IMAGE_DIMENSION = 8000             # 8000 px
WHITE_PIXEL = 255
DEFAULT_BORDER_PAD = 16
MIN_OCR_DIMENSION = 160
WIDE_STRIP_MIN_W = 500
WIDE_STRIP_MAX_H = 360
UPSCALE_FACTOR = 2.0
SHARPEN_SIGMA = 1.2
SHARPEN_ALPHA = 1.5
SHARPEN_BETA = -0.5
MIN_BLOCK_SIZE = 15
MAX_BLOCK_SIZE = 51
BLOCK_SCALE_DIVISOR = 16
MAX_SKEW_DEG = 25.0
MIN_SKEW_DEG = 0.3
HOUGH_THRESHOLD = 40
HOUGH_MIN_LEN_FLOOR = 20
HOUGH_WIDTH_DIVISOR = 10
HOUGH_MAX_GAP = 20
DEG_TO_RAD = np.pi / 180.0
MORPH_KERNEL_SIZE = (25, 3)
RED_HUE_LOW_MAX = 15
RED_HUE_HIGH_MIN = 160
RED_MIN_SAT = 150
RED_MIN_CHROMA = 100
COLOR_MIN_SAT = 165
COLOR_MIN_CHROMA = 120
COLOR_MIN_VAL = 145
MIN_SCRIBBLE_SPAN = 20
INPAINT_RADIUS = 2
STEM_BRIDGE_KERNEL = (1, 5)
THICK_CORE_KERNEL = (7, 7)


DARK_POLARITY_THRESHOLD = 127.0


class ImageProcessor:
    """
    Image Preprocessing Pipeline using OpenCV & NumPy.
    Provides decoupled static utility methods for image cleanup, 
    annotation removal, contrast enhancement, and deskewing.
    """

    @staticmethod
    def load_image(image_input: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """Converts various image inputs to BGR OpenCV NumPy array, with Unicode path support and size guards."""
        if isinstance(image_input, str):
            if os.path.exists(image_input) and os.path.getsize(image_input) > MAX_FILE_SIZE_BYTES:
                raise ValueError(f"Görsel dosya boyutu çok büyük (Maksimum 50 MB): {image_input}")

            # np.fromfile + cv2.imdecode handles Unicode / non-ASCII Turkish paths cleanly on Windows
            data = np.fromfile(image_input, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Could not read image from path: {image_input}")
        elif isinstance(image_input, Image.Image):
            img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            img = image_input.copy()
        else:
            raise TypeError(f"Unsupported image type: {type(image_input)}")

        if img.shape[0] > MAX_IMAGE_DIMENSION or img.shape[1] > MAX_IMAGE_DIMENSION:
            raise ValueError(f"Görsel boyutları çok yüksek ({img.shape[1]}x{img.shape[0]}). Maksimum izin verilen: 8000x8000 px.")
        return img

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """Converts BGR image to single channel grayscale."""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def get_background_color(image: np.ndarray) -> Union[int, Tuple[int, int, int]]:
        """Samples perimeter edge pixels to determine dominant background color."""
        h, w = image.shape[:2]
        if h <= 2 or w <= 2:
            return WHITE_PIXEL if len(image.shape) == 2 else (WHITE_PIXEL, WHITE_PIXEL, WHITE_PIXEL)
        corners = [image[0, 0], image[0, w - 1], image[h - 1, 0], image[h - 1, w - 1]]
        if len(image.shape) == 2:
            return int(np.median([int(c) for c in corners]))
        med = np.median(corners, axis=0).astype(int)
        return (int(med[0]), int(med[1]), int(med[2]))

    @staticmethod
    def is_dark_image(image: np.ndarray) -> bool:
        """Determines if the image has a predominantly dark background."""
        gray = ImageProcessor.to_grayscale(image)
        h, w = gray.shape[:2]
        if h > 4 and w > 4:
            border = np.concatenate([gray[0, :], gray[h - 1, :], gray[:, 0], gray[:, w - 1]])
            return float(np.median(border)) < DARK_POLARITY_THRESHOLD
        return float(np.mean(gray)) < DARK_POLARITY_THRESHOLD

    @staticmethod
    def invert_if_dark(image: np.ndarray) -> np.ndarray:
        """Inverts pixel intensities if the image has a dark background so OCR receives dark-on-light text."""
        if ImageProcessor.is_dark_image(image):
            return cv2.bitwise_not(image)
        return image

    @staticmethod
    def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)."""
        gray = ImageProcessor.to_grayscale(image)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(gray)

    @staticmethod
    def denoise(image: np.ndarray, h: float = 8.0) -> np.ndarray:
        """Applies gentle Non-Local Means Denoising preserving character edges and diacritics."""
        gray = ImageProcessor.to_grayscale(image)
        return cv2.fastNlMeansDenoising(gray, None, h=h, templateWindowSize=7, searchWindowSize=21)

    @staticmethod
    def sharpen(image: np.ndarray) -> np.ndarray:
        """Applies unsharp masking to crisp up blurry or upscaled text edges."""
        blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=SHARPEN_SIGMA)
        return cv2.addWeighted(image, SHARPEN_ALPHA, blurred, SHARPEN_BETA, 0)

    @staticmethod
    def add_border_padding(image: np.ndarray, pad: int = DEFAULT_BORDER_PAD, color: Optional[Any] = None) -> np.ndarray:
        """Adds natural border padding matching image background so OCR detectors do not miss edge-touching characters."""
        if pad <= 0:
            return image
        border_val = color if color is not None else ImageProcessor.get_background_color(image)
        return cv2.copyMakeBorder(
            image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=border_val
        )

    @staticmethod
    def prepare_for_ocr_with_transform(image: np.ndarray, pad: int = DEFAULT_BORDER_PAD) -> Tuple[np.ndarray, float, int]:
        """
        Upscales small crops or low-height wide strips and adds border margin for optimal OCR recognition.
        Returns (prepared_image, scale, pad) so detected coordinates can be mapped back to the input image space.
        """
        img = image.copy()
        h, w = img.shape[:2]
        scale, applied_pad = 1.0, 0
        is_tiny = h > 0 and w > 0 and (h < MIN_OCR_DIMENSION or w < MIN_OCR_DIMENSION)
        is_wide_strip = w >= WIDE_STRIP_MIN_W and 0 < h < WIDE_STRIP_MAX_H
        if is_tiny or is_wide_strip:
            if max(h, w) * UPSCALE_FACTOR <= MAX_IMAGE_DIMENSION:
                img = cv2.resize(img, None, fx=UPSCALE_FACTOR, fy=UPSCALE_FACTOR, interpolation=cv2.INTER_CUBIC)
                scale = UPSCALE_FACTOR
                if is_tiny:
                    img = ImageProcessor.sharpen(img)
            img = ImageProcessor.add_border_padding(img, pad=pad)
            applied_pad = max(0, pad)
        return img, scale, applied_pad

    @staticmethod
    def prepare_for_ocr(image: np.ndarray, pad: int = DEFAULT_BORDER_PAD) -> np.ndarray:
        """Upscales small crops or low-height wide strips and adds border margin for optimal OCR recognition."""
        return ImageProcessor.prepare_for_ocr_with_transform(image, pad)[0]

    @staticmethod
    def restore_details_coordinates(details: List[Dict[str, Any]], scale: float, pad: int) -> List[Dict[str, Any]]:
        """Maps bounding boxes detected on a prepare_for_ocr image back to the original image coordinates."""
        if scale == 1.0 and pad == 0:
            return details
        restored = []
        for d in details:
            item = dict(d)
            item["bbox"] = [[(pt[0] - pad) / scale, (pt[1] - pad) / scale] for pt in d.get("bbox", [])]
            restored.append(item)
        return restored

    @staticmethod
    def shift_details_coordinates(details: List[Dict[str, Any]], offset_x: float, offset_y: float) -> List[Dict[str, Any]]:
        """Offsets crop-space bounding boxes back into the full image coordinate space."""
        if not offset_x and not offset_y:
            return details
        shifted = []
        for d in details:
            item = dict(d)
            item["bbox"] = [[pt[0] + offset_x, pt[1] + offset_y] for pt in d.get("bbox", [])]
            shifted.append(item)
        return shifted

    @staticmethod
    def binarize_adaptive(image: np.ndarray, block_size: int = 0, c: int = 8) -> np.ndarray:
        """Applies resolution-aware adaptive Gaussian thresholding for crisp black & white text."""
        gray = ImageProcessor.to_grayscale(image)
        if block_size <= 0:
            min_dim = min(gray.shape[:2])
            block_size = max(MIN_BLOCK_SIZE, min(MAX_BLOCK_SIZE, (min_dim // BLOCK_SCALE_DIVISOR) | 1))
        elif block_size % 2 == 0:
            block_size += 1
        return cv2.adaptiveThreshold(
            gray, WHITE_PIXEL, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
        )

    @staticmethod
    def _build_scribble_mask(image: np.ndarray, remove_red: bool, remove_blue: bool) -> np.ndarray:
        """Builds a connected-component filtered mask of high-chroma MS Paint lines, shapes, and annotations."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        b, g, r = cv2.split(image)
        max_c = np.maximum(np.maximum(r, g), b)
        chroma = max_c.astype(np.int16) - np.minimum(np.minimum(r, g), b).astype(np.int16)
        hue, sat = hsv[:, :, 0], hsv[:, :, 1]

        raw_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        if remove_red:
            is_red = ((hue <= RED_HUE_LOW_MAX) | (hue >= RED_HUE_HIGH_MIN)) & (sat >= RED_MIN_SAT) & (chroma >= RED_MIN_CHROMA)
            raw_mask[is_red] = WHITE_PIXEL
        if remove_blue:
            is_other = (hue > RED_HUE_LOW_MAX) & (hue < RED_HUE_HIGH_MIN) & (sat >= COLOR_MIN_SAT) & (chroma >= COLOR_MIN_CHROMA) & (max_c >= COLOR_MIN_VAL)
            raw_mask[is_other] = WHITE_PIXEL

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(raw_mask)
        scribble_mask = np.zeros_like(raw_mask)
        for idx in range(1, num_labels):
            if max(stats[idx, cv2.CC_STAT_WIDTH], stats[idx, cv2.CC_STAT_HEIGHT]) > MIN_SCRIBBLE_SPAN:
                scribble_mask[labels == idx] = WHITE_PIXEL
        return scribble_mask

    @staticmethod
    def remove_color_annotations(image: np.ndarray, remove_red: bool = True, remove_blue: bool = True) -> np.ndarray:
        """
        Removes colored Paint lines, shapes, and highlighters via chroma/connected-component masking,
        and reconstructs occluded character stems using Fast Marching Telea inpainting + vertical morphology.
        """
        if len(image.shape) == 2:
            return image

        scribble_mask = ImageProcessor._build_scribble_mask(image, remove_red, remove_blue)
        gray = ImageProcessor.to_grayscale(image)
        if not np.any(scribble_mask > 0):
            return gray

        telea = cv2.inpaint(gray, scribble_mask, INPAINT_RADIUS, cv2.INPAINT_TELEA)
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, STEM_BRIDGE_KERNEL)
        morph_op = cv2.MORPH_CLOSE if ImageProcessor.is_dark_image(image) else cv2.MORPH_OPEN
        v_bridged = cv2.morphologyEx(telea, morph_op, v_kernel)

        result = gray.copy()
        masked = scribble_mask > 0
        result[masked] = ((telea[masked].astype(np.uint16) + v_bridged[masked].astype(np.uint16)) // 2).astype(np.uint8)
        core_thick = cv2.erode(scribble_mask, np.ones(THICK_CORE_KERNEL, np.uint8))
        background = int(ImageProcessor.get_background_color(gray))
        result[core_thick > 0] = background
        return result

    @staticmethod
    def _estimate_skew_angle(gray: np.ndarray) -> float:
        """Estimates text baseline skew angle in degrees using morphological line connection and Hough lines."""
        # Metin her zaman beyaz (ön plan) maske olmalı: açık zeminde koyu metin ters çevrilir, koyu zeminde olduğu gibi kalır.
        text_gray = gray if ImageProcessor.is_dark_image(gray) else cv2.bitwise_not(gray)
        thresh = cv2.threshold(text_gray, 0, WHITE_PIXEL, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_KERNEL_SIZE)
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        w = gray.shape[1]
        lines = cv2.HoughLinesP(
            dilated, 1, DEG_TO_RAD, threshold=HOUGH_THRESHOLD,
            minLineLength=max(HOUGH_MIN_LEN_FLOOR, w // HOUGH_WIDTH_DIVISOR), maxLineGap=HOUGH_MAX_GAP
        )
        if lines is None:
            return 0.0

        angles = []
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            if x2 != x1:
                deg = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                if -MAX_SKEW_DEG <= deg <= MAX_SKEW_DEG:
                    angles.append(deg)
        return float(np.median(angles)) if angles else 0.0

    @staticmethod
    def deskew(image: np.ndarray) -> np.ndarray:
        """Detects text line inclination angle and deskews the image with clean white borders."""
        gray = ImageProcessor.to_grayscale(image)
        angle = ImageProcessor._estimate_skew_angle(gray)
        if abs(angle) < MIN_SKEW_DEG or abs(angle) > MAX_SKEW_DEG:
            return image

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        border_val = ImageProcessor.get_background_color(image)
        return cv2.warpAffine(
            image, rot_mat, (w, h), flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT, borderValue=border_val
        )

    @staticmethod
    def crop_roi(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Crops a region of interest (ROI) from image."""
        h_img, w_img = image.shape[:2]
        x1 = max(0, min(x, w_img))
        y1 = max(0, min(y, h_img))
        x2 = max(0, min(x + width, w_img))
        y2 = max(0, min(y + height, h_img))
        return image[y1:y2, x1:x2]
