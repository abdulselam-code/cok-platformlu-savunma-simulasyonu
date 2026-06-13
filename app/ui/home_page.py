"""Uygulamanın başlangıç sayfası."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    """Ana ekranda görünen başlangıç paneli."""

    simulation_requested = Signal()
    about_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 36, 40, 36)
        root_layout.setSpacing(18)

        root_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        panel = QFrame(self)
        panel.setObjectName("HomePanel")
        panel.setMaximumWidth(860)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(36, 32, 36, 32)
        panel_layout.setSpacing(20)

        eyebrow_label = QLabel("GRAFİK PROGRAMLAMA FİNAL PROJESİ", panel)
        eyebrow_label.setObjectName("EyebrowLabel")

        title_label = QLabel("ÇOK PLATFORMLU SAVUNMA SİSTEMLERİ", panel)
        title_label.setObjectName("HeroTitleLabel")
        title_label.setWordWrap(True)

        subtitle_label = QLabel(
            "Çevresel etkiler altında 2B atış ve yörünge simülasyonu",
            panel,
        )
        subtitle_label.setObjectName("HeroSubtitleLabel")
        subtitle_label.setWordWrap(True)

        panel_layout.addWidget(eyebrow_label)
        panel_layout.addWidget(title_label)
        panel_layout.addWidget(subtitle_label)

        status_frame = QFrame(panel)
        status_frame.setObjectName("StatusFrame")
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(18, 16, 18, 16)
        status_layout.setSpacing(24)

        status_items = (
            ("Durum", "Başlangıç iskeleti"),
            ("Teknoloji", "Python 3.13 + PySide6"),
            ("Arayüz", "Koyu mühendislik paneli"),
        )

        for caption, value in status_items:
            column = QVBoxLayout()
            value_label = QLabel(value, status_frame)
            value_label.setObjectName("StatusValueLabel")
            caption_label = QLabel(caption, status_frame)
            caption_label.setObjectName("StatusCaptionLabel")
            column.addWidget(value_label)
            column.addWidget(caption_label)
            status_layout.addLayout(column)

        panel_layout.addWidget(status_frame)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(14)

        start_button = QPushButton("Simülasyonu Başlat", panel)
        start_button.setObjectName("PrimaryButton")
        start_button.clicked.connect(self.simulation_requested.emit)

        about_button = QPushButton("Proje Hakkında", panel)
        about_button.clicked.connect(self.about_requested.emit)

        exit_button = QPushButton("Çıkış", panel)
        exit_button.setObjectName("DangerButton")
        exit_button.clicked.connect(self.exit_requested.emit)

        buttons_layout.addWidget(start_button)
        buttons_layout.addWidget(about_button)
        buttons_layout.addWidget(exit_button)

        panel_layout.addLayout(buttons_layout)

        root_layout.addWidget(panel, 0, Qt.AlignmentFlag.AlignHCenter)
        root_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
