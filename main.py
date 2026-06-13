"""Uygulamanın tek giriş noktası."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


LOG_FILE = Path("startup.log")


def configure_logging() -> None:
    """Başlangıç hatalarını dosyaya kaydeder."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
    )


def main() -> int:
    """Qt uygulamasını güvenli biçimde başlatır."""

    configure_logging()

    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from app.main_window import MainWindow
        from app.styles import apply_application_style
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "bilinmeyen"
        logging.error("Gerekli bağımlılık bulunamadı: %s", missing_module)
        print(
            "Uygulama başlatılamadı. Gerekli bağımlılık eksik: "
            f"{missing_module}.",
            file=sys.stderr,
        )
        return 1
    except Exception:
        logging.exception("Uygulama modülleri yüklenemedi.")
        print("Uygulama başlatılamadı.", file=sys.stderr)
        return 1

    try:
        application = QApplication.instance()
        if application is None:
            application = QApplication(sys.argv)

        application.setApplicationName("Çok Platformlu Savunma Sistemleri Simülasyonu")
        application.setOrganizationName("Grafik Programlama")
        application.setQuitOnLastWindowClosed(True)
        apply_application_style(application)

        window = MainWindow()
        window.show()
        return application.exec()
    except Exception:
        logging.exception("Uygulama başlatılırken beklenmeyen bir hata oluştu.")
        try:
            QMessageBox.critical(
                None,
                "Başlatma Hatası",
                "Uygulama başlatılırken beklenmeyen bir hata oluştu.",
            )
        except Exception:
            print(
                "Uygulama başlatılırken beklenmeyen bir hata oluştu.",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
