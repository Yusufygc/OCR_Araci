"""
Başsız kendi kendini sınama (`OCRAraci.exe --selftest`).

Paketlenmiş exe'nin çalışma zamanı bağımlılıklarının (torch, torchvision özel işlemleri, easyocr, OpenCV, python-docx)
gerçekten yüklenip çalıştığını doğrular. Pencere açmaz; sonuç çıkış koduyla (0 = tamam) ve isteğe bağlı rapor dosyasıyla verilir.
Gerekçe: exe'nin "açık kalması" yetmez; eksik bir binary, hata penceresiyle de süreci açık tutar (docs/wiki/exe_distribution.md).
"""
from typing import Callable, List, Optional, Tuple

SELFTEST_FLAG = "--selftest"

Check = Tuple[str, Callable[[], str]]


def _check_torchvision_ops() -> str:
    import torch
    import torchvision

    boxes = torch.tensor([[0.0, 0.0, 10.0, 10.0], [1.0, 1.0, 11.0, 11.0], [50.0, 50.0, 60.0, 60.0]])
    scores = torch.tensor([0.9, 0.8, 0.7])
    kept = torchvision.ops.nms(boxes, scores, 0.5)
    if len(kept) != 2:
        raise RuntimeError(f"nms beklenmeyen sonuç verdi: {kept.tolist()}")
    return f"torch {torch.__version__}, torchvision {torchvision.__version__}, nms tamam"


def _check_easyocr_engine() -> str:
    from src.core.factories.ocr_factory import OCREngineFactory

    engine = OCREngineFactory.get_engine("easyocr")
    if not engine.is_available:
        raise RuntimeError("EasyOCR motoru yüklenemedi")
    return "EasyOCR motoru hazır"


def _check_image_pipeline() -> str:
    import numpy as np

    from src.core.processing.image_processor import ImageProcessor

    image = np.full((64, 160, 3), 255, dtype=np.uint8)
    prepared = ImageProcessor.prepare_for_ocr(ImageProcessor.deskew(image))
    return f"OpenCV hattı tamam ({prepared.shape[1]}x{prepared.shape[0]})"


def _check_exporters() -> str:
    import docx  # noqa: F401

    from src.utils.exporters.exporter_factory import ExporterFactory

    return f"Dışa aktarıcılar: {', '.join(sorted(['txt', 'docx', 'pdf']))} ({type(ExporterFactory.get_exporter('docx')).__name__})"


CHECKS: List[Check] = [
    ("torchvision", _check_torchvision_ops),
    ("easyocr", _check_easyocr_engine),
    ("görüntü işleme", _check_image_pipeline),
    ("dışa aktarıcılar", _check_exporters),
]


def run_selftest(report_path: Optional[str] = None, checks: Optional[List[Check]] = None) -> int:
    """Tüm denetimleri çalıştırır; hepsi geçerse 0, aksi halde 1 döner. Rapor satırları dosyaya/standart çıktıya yazılır."""
    lines: List[str] = []
    failed = False
    for name, check in (checks if checks is not None else CHECKS):
        try:
            lines.append(f"OK    {name}: {check()}")
        except Exception as error:  # her denetim bağımsız raporlanır
            failed = True
            lines.append(f"HATA  {name}: {type(error).__name__}: {error}")
    lines.append("SONUC: BASARISIZ" if failed else "SONUC: BASARILI")
    report = "\n".join(lines) + "\n"
    if report_path:
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write(report)
    else:
        print(report)
    return 1 if failed else 0
