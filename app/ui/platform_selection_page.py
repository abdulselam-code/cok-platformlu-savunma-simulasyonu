"""Platform seçim sayfası."""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class PlatformSelectionPage(QWidget):
    """Savunma platformlarının seçildiği sayfa."""

    back_requested = Signal()
    platform_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        """Sayfanın kullanıcı arayüzünü oluşturur."""
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 34, 40, 34)
        root_layout.setSpacing(20)

        header_panel = QFrame(self)
        header_panel.setObjectName("HomePanel")
        header_layout = QVBoxLayout(header_panel)
        header_layout.setContentsMargins(28, 24, 28, 24)
        header_layout.setSpacing(10)

        eyebrow_label = QLabel("SİMÜLASYON MERKEZİ", header_panel)
        eyebrow_label.setObjectName("EyebrowLabel")

        title_label = QLabel("PLATFORM SEÇİMİ", header_panel)
        title_label.setObjectName("HeroTitleLabel")
        title_label.setWordWrap(True)

        subtitle_label = QLabel(
            "Simülasyonunu başlatmak için bir savunma platformu seç.",
            header_panel,
        )
        subtitle_label.setObjectName("HeroSubtitleLabel")
        subtitle_label.setWordWrap(True)

        header_layout.addWidget(eyebrow_label)
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)

        root_layout.addWidget(header_panel)

        grid_container = QFrame(self)
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(18)
        grid_layout.setVerticalSpacing(18)

        platform_cards = (
            (
                "HAVA",
                "Hava Platformu",
                "Yükseklik, uçuş hızı ve rüzgâr etkisi altında bırakma simülasyonu.",
                "aircraft",
            ),
            (
                "KARA",
                "Kara Platformu",
                "Namlu açısı, ilk hız ve arazi koşulları altında balistik atış simülasyonu.",
                "tank",
            ),
            (
                "DENİZ",
                "Deniz Üstü Platformu",
                "Dalga, rüzgâr ve gemi hareketinin etkilediği atış simülasyonu.",
                "ship",
            ),
            (
                "SU ALTI",
                "Deniz Altı Platformu",
                "Derinlik ve su akıntısı altında hareket eden su altı aracı simülasyonu.",
                "submarine",
            ),
        )

        positions = ((0, 0), (0, 1), (1, 0), (1, 1))
        for position, platform_info in zip(positions, platform_cards, strict=True):
            card = self._create_platform_card(*platform_info)
            grid_layout.addWidget(card, *position)

        root_layout.addWidget(grid_container)

        bottom_row = QHBoxLayout()
        bottom_row.addItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
        )

        back_button = QPushButton("Ana Sayfaya Dön", self)
        back_button.setObjectName("DangerButton")
        back_button.clicked.connect(self.back_requested.emit)
        bottom_row.addWidget(back_button)

        root_layout.addLayout(bottom_row)
        root_layout.setStretch(1, 1)

    def _create_platform_card(
        self,
        category: str,
        title: str,
        description: str,
        platform_id: str,
    ) -> QFrame:
        """Tek bir platform kartı üretir."""
        card = QFrame(self)
        card.setObjectName("StatusFrame")
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        card.setMinimumHeight(190)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        category_label = QLabel(category, card)
        category_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        category_label.setWordWrap(True)

        title_label = QLabel(title, card)
        title_label.setWordWrap(True)
        title_label.setObjectName("StatusValueLabel")

        description_label = QLabel(description, card)
        description_label.setWordWrap(True)
        description_label.setObjectName("StatusCaptionLabel")

        select_button = QPushButton("Platformu Seç", card)
        select_button.setObjectName("PrimaryButton")
        select_button.clicked.connect(partial(self.platform_selected.emit, platform_id))

        card_layout.addWidget(category_label)
        card_layout.addWidget(title_label)
        card_layout.addWidget(description_label)
        card_layout.addStretch(1)
        card_layout.addWidget(select_button)

        return card