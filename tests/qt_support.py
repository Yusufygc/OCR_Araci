"""
Qt testleri için ortak yardımcı: yorumlayıcı kapanırken Qt nesnelerini doğru sırayla yok eder.

Neden: pencereler/iş parçacıkları testlerden sonra canlı kalırsa, Python kapanışında nesneler QApplication'dan sonra
rastgele sırayla silinir ve Linux'ta çıkışta segfault olabilir ("QObject: shared QObject was deleted directly").
Testler geçse bile CI çıkış kodu 139 olur. Bu modül içe aktarıldığında bir kez `atexit` kancası kaydeder.
"""
import atexit

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

_registered = False


def dispose_qt_objects() -> None:
    """Açık üst düzey pencereleri kapatıp siler ve bekleyen silme olaylarını işler."""
    app = QApplication.instance()
    if app is None:
        return
    for widget in QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    app.processEvents()
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()


def ensure_qt_cleanup() -> None:
    """Çıkış temizliğini bir kez kaydeder."""
    global _registered
    if not _registered:
        atexit.register(dispose_qt_objects)
        _registered = True


ensure_qt_cleanup()
