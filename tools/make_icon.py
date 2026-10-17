"""
OCR Aracı uygulama ikonunu üretir (Pillow ile, dış dosya gerekmez).

    python tools/make_icon.py

Çıktılar:
  packaging/app_icon.ico        exe, kurulum sihirbazı ve kısayol ikonu (16-256 px)
  src/ui/assets/app_icon.png    pencere / görev çubuğu ikonu (256 px)

Tasarım: koyu zemin, açık renkli belge (metin satırları) ve etrafında yeşil (#00e676) tarama çerçevesi + tarama çizgisi.
ICO exe özetine girer (docs/wiki/exe_distribution.md); değiştirirsen kararlı exe'yi bilerek değiştirme adımlarını izle.
"""
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ICO_PATH = ROOT / "packaging" / "app_icon.ico"
PNG_PATH = ROOT / "src" / "ui" / "assets" / "app_icon.png"

CANVAS = 1024
ICO_SIZES: List[Tuple[int, int]] = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
BACKGROUND = (20, 24, 26, 255)
BACKGROUND_EDGE = (0, 230, 118, 255)
PAGE = (236, 240, 241, 255)
TEXT_LINE = (96, 110, 118, 255)
ACCENT = (0, 230, 118, 255)
CORNER_RADIUS = 210
PAGE_BOX = (276, 222, 748, 802)
FRAME_BOX = (170, 150, 854, 874)
FRAME_ARM = 150
FRAME_STROKE = 62
TEXT_LINES = ((350, 330, 674), (350, 430, 674), (350, 530, 600), (350, 630, 674), (350, 730, 520))
SCAN_Y = 580


def _draw_background(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, CANVAS - 1, CANVAS - 1), CORNER_RADIUS, fill=BACKGROUND_EDGE)
    inset = 22
    draw.rounded_rectangle(
        (inset, inset, CANVAS - 1 - inset, CANVAS - 1 - inset), CORNER_RADIUS - inset, fill=BACKGROUND
    )


def _draw_page(image: Image.Image) -> None:
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(PAGE_BOX, 56, fill=PAGE)
    for x1, y, x2 in TEXT_LINES:
        draw.rounded_rectangle((x1, y - 22, x2, y + 22), 22, fill=TEXT_LINE)


def _draw_frame(image: Image.Image) -> None:
    """Dört köşe parantezi: tarama/OCR çerçevesi."""
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = FRAME_BOX
    half = FRAME_STROKE // 2
    for x, y, dx, dy in ((left, top, 1, 1), (right, top, -1, 1), (left, bottom, 1, -1), (right, bottom, -1, -1)):
        draw.line((x, y, x + dx * FRAME_ARM, y), fill=ACCENT, width=FRAME_STROKE)
        draw.line((x, y, x, y + dy * FRAME_ARM), fill=ACCENT, width=FRAME_STROKE)
        draw.ellipse((x - half, y - half, x + half, y + half), fill=ACCENT)


def _draw_scan_line(image: Image.Image) -> Image.Image:
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle((FRAME_BOX[0] + 20, SCAN_Y - 38, FRAME_BOX[2] - 20, SCAN_Y + 38), 38, fill=(0, 230, 118, 120))
    image = Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(26)))
    ImageDraw.Draw(image).rounded_rectangle(
        (FRAME_BOX[0] + 20, SCAN_Y - 17, FRAME_BOX[2] - 20, SCAN_Y + 17), 17, fill=ACCENT
    )
    return image


def render(size: int = CANVAS) -> Image.Image:
    """İkonu CANVAS çözünürlüğünde çizip `size`'a küçültür (kenar yumuşatma için)."""
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    _draw_background(image)
    _draw_page(image)
    _draw_frame(image)
    image = _draw_scan_line(image)
    return image if size == CANVAS else image.resize((size, size), Image.LANCZOS)


def main() -> None:
    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    render(256).save(ICO_PATH, format="ICO", sizes=ICO_SIZES)
    render(256).save(PNG_PATH, format="PNG")
    print(f"Yazıldı: {ICO_PATH}\nYazıldı: {PNG_PATH}")


if __name__ == "__main__":
    main()
