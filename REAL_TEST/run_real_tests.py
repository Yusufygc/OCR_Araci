import os
import sys
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.core.processing.image_processor import ImageProcessor
from src.core.factories.ocr_factory import OCREngineFactory
from src.utils.exporters.exporter_factory import ExporterFactory

PERCENT_SCALE = 100.0
WHITE_VAL = 255
DARK_TEXT_COLOR = (20, 20, 20)
RED_PAINT = (0, 0, 255)
DARK_RED_PAINT = (0, 0, 220)
BLUE_PAINT = (255, 60, 0)
GREEN_PAINT = (0, 190, 0)
YELLOW_PAINT = (0, 230, 255)
MAGENTA_PAINT = (255, 0, 255)
SYNTH_WIDTH = 960
SYNTH_HEIGHT = 380
SYNTH_FONT_SIZE = 22
SYNTH_SKEW_ANGLE = -4.0

PAINT_COORDS_LIGHT = {
    "l1": ((10, 52), (650, 52)),
    "l2": ((10, 125), (750, 125)),
    "diag": ((100, 35), (450, 165)),
    "rect": ((20, 70), (420, 145)),
    "circle": ((550, 110), 45),
    "yellow": ((15, 195), (600, 195)),
}

PAINT_COORDS_DARK = {
    "l1": ((250, 95), (820, 95)),
    "l2": ((250, 145), (820, 145)),
    "rect": ((245, 200), (520, 340)),
    "circle": ((650, 270), 55),
    "diag": ((250, 60), (600, 180)),
}

OPEN_SOURCE_LINES = [
    "Acik Kaynak Ansiklopedi Metni - Optik Karakter Tanima Testi",
    "Bilgisayarli goru ve derin ogrenme yontemleri, taranmis belgelerdeki",
    "egri satirlari ve renkli kalem ciziklerini temizlemek icin kullanilir.",
    "Hough donusumu egim acisini bulurken, Telea inpainting algoritmasi",
    "harflerin uzerindeki kirmizi ve mavi sekilleri dokuyu koruyarak siler.",
]

TEST_DATA = [
    {
        "id": "sample1",
        "filename": "sample1_dark_ui1.png",
        "name": "Koyu Tema UI Metni 1 (Dinamik Ekran / Ortalama)",
        "pipeline": "raw",
        "ground_truth_keywords": ["Dinamik Ekran Boyutu", "MainWindow", "Merkezine", "showEvent", "Wiki"]
    },
    {
        "id": "sample2",
        "filename": "sample2_dark_ui2.png",
        "name": "Koyu Tema UI Metni 2 (Görüntü Önişleme Adımları)",
        "pipeline": "raw",
        "ground_truth_keywords": ["Görüntü Önişleme", "deskew", "remove_color_annotations", "binarize_adaptive", "prepare_for_ocr"]
    },
    {
        "id": "sample3",
        "filename": "sample3_search_snippet.png",
        "name": "Arama Sonucu Snippet (Film/Dizi Başlığı & Açıklama)",
        "pipeline": "raw",
        "ground_truth_keywords": ["Film izle Hell", "Soulm8te", "Türkçe Dublaj", "yapay zekayı", "kaos"]
    },
    {
        "id": "sample4",
        "filename": "sample4_wiki_document.png",
        "name": "Açık Tema Doküman (Wikipedia Hukuk Metni)",
        "pipeline": "raw",
        "ground_truth_keywords": ["Program çeşitleri", "Bankacılık", "Vergi Hukuku", "Kamu Hukuku", "Özel Hukuk"]
    },
    {
        "id": "sample5",
        "filename": "sample5_video_player.png",
        "name": "Koyu Video Oynatıcı Arayüzü ve Alt Banner",
        "pipeline": "raw",
        "ground_truth_keywords": ["Türkçe Dublaj", "Altyazılı", "1:40:10", "Yatırım", "Turnuvalar"]
    },
    {
        "id": "sample6",
        "filename": "sample6_movie_info.png",
        "name": "Afişli Film Bilgi Kartı (Çok Sütunlu Koyu UI)",
        "pipeline": "raw",
        "ground_truth_keywords": ["Filminin Bilgileri", "teknoloji devi", "yapay zeka", "99 dakika", "Gerilim"]
    },
    {
        "id": "sample7",
        "filename": "sample7_paint_scribbles_light.png",
        "name": "MS Paint Çizikli & Şekilli Açık Doküman (Kırmızı Çizgi, Mavi Kutu, Yeşil Daire)",
        "pipeline": "clean_paint",
        "ground_truth_keywords": ["Program çeşitleri", "Bankacılık", "Rekabet Hukuku", "University", "Hakları"]
    },
    {
        "id": "sample8",
        "filename": "sample8_paint_scribbles_dark.png",
        "name": "MS Paint Çizikli & Şekilli Koyu Film Kartı (Renkli Karalama & Şekiller)",
        "pipeline": "clean_paint",
        "ground_truth_keywords": ["Filminin Bilgileri", "teknoloji devi", "yapay zeka", "99 dakika", "14,573"]
    },
    {
        "id": "sample9",
        "filename": "sample9_opensource_paint_skew.png",
        "name": "Açık Kaynak Metin + Eğik Belge (-4°) + MS Paint Çizik & Şekiller",
        "pipeline": "clean_paint_and_deskew",
        "ground_truth_keywords": ["Acik Kaynak", "Bilgisayarli goru", "derin ogrenme", "Hough donusumu", "Telea inpainting"]
    },
    {
        "id": "sample10",
        "filename": "sample10_diagram_clean.png",
        "name": "Çok Sütunlu Finansal Makine Öğrenmesi Şeması ve Kartları (Bölgesel Tarama)",
        "pipeline": "raw",
        "ground_truth_keywords": ["Finansal Veriler", "Sosyal Medya", "Makine Öğrenmesi", "Fiyat Tahmini", "Duygu Analizi", "Risk Profili", "Portföy Optimizasyonu"]
    },
]


def _save_unicode_png(path: str, img: np.ndarray):
    """Saves an OpenCV image safely on Windows paths."""
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)


def _generate_paint_samples(real_test_dir: str):
    """Generates MS Paint scribbled and skewed open-source test images inside REAL_TEST."""
    s4_path = os.path.join(real_test_dir, "sample4_wiki_document.png")
    if os.path.exists(s4_path):
        p_light = ImageProcessor.load_image(s4_path)
        c = PAINT_COORDS_LIGHT
        cv2.line(p_light, c["l1"][0], c["l1"][1], RED_PAINT, 2)
        cv2.line(p_light, c["l2"][0], c["l2"][1], RED_PAINT, 2)
        cv2.line(p_light, c["diag"][0], c["diag"][1], DARK_RED_PAINT, 2)
        cv2.rectangle(p_light, c["rect"][0], c["rect"][1], BLUE_PAINT, 2)
        cv2.circle(p_light, c["circle"][0], c["circle"][1], GREEN_PAINT, 2)
        cv2.line(p_light, c["yellow"][0], c["yellow"][1], YELLOW_PAINT, 2)
        _save_unicode_png(os.path.join(real_test_dir, "sample7_paint_scribbles_light.png"), p_light)

    s6_path = os.path.join(real_test_dir, "sample6_movie_info.png")
    if os.path.exists(s6_path):
        p_dark = ImageProcessor.load_image(s6_path)
        d = PAINT_COORDS_DARK
        cv2.line(p_dark, d["l1"][0], d["l1"][1], RED_PAINT, 2)
        cv2.line(p_dark, d["l2"][0], d["l2"][1], YELLOW_PAINT, 2)
        cv2.rectangle(p_dark, d["rect"][0], d["rect"][1], BLUE_PAINT, 2)
        cv2.circle(p_dark, d["circle"][0], d["circle"][1], GREEN_PAINT, 2)
        cv2.line(p_dark, d["diag"][0], d["diag"][1], MAGENTA_PAINT, 2)
        _save_unicode_png(os.path.join(real_test_dir, "sample8_paint_scribbles_dark.png"), p_dark)

    _generate_open_source_skew_paint(real_test_dir)


def _generate_open_source_skew_paint(real_test_dir: str):
    """Creates an open-source synthetic text document, skews it, and draws Paint shapes over it."""
    pil_canvas = Image.new("RGB", (SYNTH_WIDTH, SYNTH_HEIGHT), (WHITE_VAL, WHITE_VAL, WHITE_VAL))
    draw = ImageDraw.Draw(pil_canvas)
    try:
        font = ImageFont.truetype("arial.ttf", SYNTH_FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    y_pos = 45
    for line in OPEN_SOURCE_LINES:
        draw.text((45, y_pos), line, fill=DARK_TEXT_COLOR, font=font)
        y_pos += 55

    cv_doc = cv2.cvtColor(np.array(pil_canvas), cv2.COLOR_RGB2BGR)
    center = (SYNTH_WIDTH // 2, SYNTH_HEIGHT // 2)
    rot_mat = cv2.getRotationMatrix2D(center, SYNTH_SKEW_ANGLE, 1.0)
    skewed = cv2.warpAffine(
        cv_doc, rot_mat, (SYNTH_WIDTH, SYNTH_HEIGHT),
        flags=cv2.INTER_CUBIC, borderValue=(WHITE_VAL, WHITE_VAL, WHITE_VAL)
    )
    cv2.line(skewed, (40, 110), (880, 145), RED_PAINT, 2)
    cv2.rectangle(skewed, (60, 155), (520, 290), BLUE_PAINT, 2)
    cv2.circle(skewed, (720, 220), 65, GREEN_PAINT, 2)
    cv2.line(skewed, (50, 275), (860, 250), YELLOW_PAINT, 2)
    _save_unicode_png(os.path.join(real_test_dir, "sample9_opensource_paint_skew.png"), skewed)


def _apply_pipeline(cv_img: np.ndarray, pipeline: str, img_id: str, exports_dir: str) -> np.ndarray:
    """Applies the requested ImageProcessor filter pipeline and saves intermediate cleaned image."""
    if pipeline == "clean_paint":
        cleaned = ImageProcessor.remove_color_annotations(cv_img)
        _save_unicode_png(os.path.join(exports_dir, f"{img_id}_cleaned.png"), cleaned)
        return cleaned
    if pipeline == "clean_paint_and_deskew":
        cleaned = ImageProcessor.remove_color_annotations(cv_img)
        deskewed = ImageProcessor.deskew(cleaned)
        _save_unicode_png(os.path.join(exports_dir, f"{img_id}_cleaned_deskewed.png"), deskewed)
        return deskewed
    return cv_img


def _export_formats(text: str, img_id: str, engine_key: str, exports_dir: str):
    """Exports OCR text to TXT, PDF, and DOCX formats."""
    for fmt in ["txt", "pdf", "docx"]:
        out_name = f"{img_id}_{engine_key}.{fmt}"
        out_path = os.path.join(exports_dir, out_name)
        exporter = ExporterFactory.get_exporter(fmt)
        exporter.export(text, out_path)


def _evaluate_engine(engine_key: str, cv_img: np.ndarray, img_meta: dict, exports_dir: str):
    """Executes OCR with given engine, evaluates keywords, and triggers file export."""
    engine = OCREngineFactory.get_engine(engine_key)
    if img_meta["id"] == "sample10":
        from src.core.strategies.scan_factory import ScanStrategyFactory
        strategy = ScanStrategyFactory.get_strategy("block")
        result = strategy.execute(cv_img, engine, lang="tur+eng")
    else:
        result = engine.extract_text(cv_img, lang="tur+eng")

    norm_text = " ".join(result.text.split()).lower()
    matched = [kw for kw in img_meta["ground_truth_keywords"] if kw.lower() in norm_text]
    match_rate = f"{len(matched)}/{len(img_meta['ground_truth_keywords'])}"

    if result.text:
        _export_formats(result.text, img_meta["id"], engine_key, exports_dir)

    conf_pct = result.confidence * PERCENT_SCALE
    status_str = "BAŞARILI" if result.success else "HATA"
    summary_row = f"| {img_meta['filename']} | {engine.name} | {result.processing_time:.2f}s | {conf_pct:.1f}% | {status_str} | {match_rate} |"
    return result, matched, match_rate, summary_row


def _build_markdown_report(real_test_dir: str, summary_table: list, details: list):
    """Writes the formatted markdown report to REPORT.md."""
    lines = [
        "# GERÇEK KULLANICI TESTİ, PAINT KARALAMA TEMİZLEME VE OCR KALİTE RAPORU",
        f"**Test Tarihi:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Test Klasörü:** `{real_test_dir}`\n",
        "---\n",
        "### Test Özeti Tablosu (10 Senaryo x 2 Motor = 20 OCR Koşumu)\n" + "\n".join(summary_table) + "\n\n---\n"
    ]
    lines.extend(details)
    report_path = os.path.join(real_test_dir, "REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_tests():
    """Main orchestrator for real user testing, Paint scribble removal, and reporting."""
    real_test_dir = os.path.dirname(os.path.abspath(__file__))
    exports_dir = os.path.join(real_test_dir, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    _generate_paint_samples(real_test_dir)

    _ = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    summary_table = [
        "| Görsel | Motor | Süre (sn) | Güven (%) | Başarı | Anahtar Kelime |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    details = []
    engines = ["easyocr"] + (["tesseract"] if OCREngineFactory.get_engine("tesseract").is_available else [])

    for img_meta in TEST_DATA:
        img_path = os.path.join(real_test_dir, img_meta["filename"])
        if not os.path.exists(img_path):
            continue
        raw_img = ImageProcessor.load_image(img_path)
        proc_img = _apply_pipeline(raw_img, img_meta["pipeline"], img_meta["id"], exports_dir)
        window.canvas.set_cv_image(proc_img)
        details.append(f"## Görsel: {img_meta['name']}\n- **Dosya:** `{img_meta['filename']}` (`Pipeline: {img_meta['pipeline']}`)\n")

        for key in engines:
            res, matched, rate, row = _evaluate_engine(key, proc_img, img_meta, exports_dir)
            summary_table.append(row)
            name = OCREngineFactory.get_engine(key).name
            details.extend([
                f"### Motor Çıktısı: {name}",
                f"- **İşlem Süresi:** {res.processing_time:.2f} saniye",
                f"- **Ortalama Güven Skoru:** {res.confidence * PERCENT_SCALE:.2f}%",
                f"- **Anahtar Kelime Eşleşmesi:** {rate} (`{', '.join(matched)}`)",
                "```text", res.text.strip(), "```\n"
            ])
        details.append("---\n")

    _build_markdown_report(real_test_dir, summary_table, details)


if __name__ == "__main__":
    run_tests()
