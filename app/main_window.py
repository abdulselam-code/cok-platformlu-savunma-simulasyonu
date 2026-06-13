"""Ana pencere ve sayfa geçişleri."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
)

from app.ui.home_page import HomePage
from app.ui.platform_selection_page import PlatformSelectionPage


WINDOW_TITLE = "Çok Platformlu Savunma Sistemleri Simülasyonu"


class MainWindow(QMainWindow):
    """Uygulamanın ana penceresini ve sayfa geçişlerini yönetir."""

    _PLATFORM_NAMES: dict[str, str] = {
        "aircraft": "Hava Platformu",
        "tank": "Kara Platformu",
        "ship": "Deniz Üstü Platformu",
        "submarine": "Deniz Altı Platformu",
    }

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1200, 750)
        self.setMinimumSize(950, 650)

        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        self._home_page = HomePage(self)
        self._platform_selection_page = PlatformSelectionPage(self)

        self._stack.addWidget(self._home_page)
        self._stack.addWidget(self._platform_selection_page)

        self._connect_signals()
        self._show_home_page()

    def _connect_signals(self) -> None:
        """Sayfalardaki sinyalleri yalnızca bir kez bağlar."""
        self._home_page.simulation_requested.connect(
            self._show_platform_selection_page
        )
        self._home_page.about_requested.connect(self._show_about_message)
        self._home_page.exit_requested.connect(self._request_exit)

        self._platform_selection_page.back_requested.connect(
            self._show_home_page
        )
        self._platform_selection_page.platform_selected.connect(
            self._handle_platform_selected
        )

    def _show_home_page(self) -> None:
        """Ana sayfaya geçer."""
        self._stack.setCurrentWidget(self._home_page)

    def _show_platform_selection_page(self) -> None:
        """Platform seçim sayfasına geçer."""
        self._stack.setCurrentWidget(self._platform_selection_page)

    def _handle_platform_selected(self, platform_id: str) -> None:
        """Seçilen platformu doğrular ve kullanıcıyı bilgilendirir."""
        platform_key = platform_id.strip().lower()
        platform_name = self._PLATFORM_NAMES.get(platform_key)

        if platform_name is None:
            QMessageBox.warning(
                self,
                "Geçersiz Seçim",
                "Geçersiz platform seçimi.",
            )
            return

        QMessageBox.information(
            self,
            "Platform Seçildi",
            (
                f"{platform_name} seçildi.\n\n"
                "Bu platformun simülasyon ekranı "
                "sonraki aşamada eklenecektir."
            ),
        )

    def _show_about_message(self) -> None:
        """Projenin amacı hakkında bilgi verir."""
        QMessageBox.information(
            self,
            "Proje Hakkında",
            (
                "Bu proje, eğitim amaçlı hazırlanmış kurgusal bir 2B fizik "
                "ve grafik programlama simülasyonudur.\n\n"
                "Uçak, tank, gemi ve denizaltı platformlarının çevresel "
                "etkiler altındaki hareketleri görselleştirilecektir."
            ),
        )

    def _request_exit(self) -> None:
        """Uygulamayı güvenli biçimde kapatır."""
        application = QApplication.instance()

        if application is not None:
            application.quit()
        else:
            self.close()