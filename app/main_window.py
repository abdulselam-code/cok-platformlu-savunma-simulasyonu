"""Ana pencere ve başlangıç gezinme yapısı."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from app.ui.home_page import HomePage


WINDOW_TITLE = "Çok Platformlu Savunma Sistemleri Simülasyonu"


class MainWindow(QMainWindow):
    """Uygulamanın ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1200, 750)
        self.setMinimumSize(950, 650)

        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)

        self._home_page = HomePage(self)
        self._stack.addWidget(self._home_page)
        self._stack.setCurrentWidget(self._home_page)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self._home_page.simulation_requested.connect(self._show_simulation_message)
        self._home_page.about_requested.connect(self._show_about_message)
        self._home_page.exit_requested.connect(self._request_exit)

    def _show_simulation_message(self) -> None:
        QMessageBox.information(
            self,
            "Bilgilendirme",
            "Platform seçim ekranı sonraki geliştirme aşamasında eklenecektir.",
        )

    def _show_about_message(self) -> None:
        QMessageBox.information(
            self,
            "Proje Hakkında",
            (
                "Bu proje, eğitim amaçlı hazırlanmış kurgusal bir 2B fizik ve "
                "grafik programlama simülasyonudur."
            ),
        )

    def _request_exit(self) -> None:
        application = QApplication.instance()
        if application is not None:
            application.quit()
            return

        self.close()
