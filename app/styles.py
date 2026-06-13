"""Uygulamanın görsel stili."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


APPLICATION_STYLE_SHEET = """
QWidget {
    color: #e6edf7;
    font-family: "Segoe UI";
    font-size: 11pt;
}

QMainWindow {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #0b1118, stop: 1 #111c2a);
}

QFrame#HomePanel {
    background-color: rgba(12, 20, 31, 0.92);
    border: 1px solid #233447;
    border-radius: 22px;
}

QFrame#StatusFrame {
    background-color: rgba(18, 28, 41, 0.95);
    border: 1px solid #27394f;
    border-radius: 14px;
}

QLabel#EyebrowLabel {
    color: #7fc7ff;
    font-size: 9.5pt;
    font-weight: 700;
    letter-spacing: 2px;
}

QLabel#HeroTitleLabel {
    color: #f4f8fc;
    font-size: 28pt;
    font-weight: 800;
    letter-spacing: 1px;
}

QLabel#HeroSubtitleLabel {
    color: #aebdcc;
    font-size: 12pt;
}

QLabel#StatusValueLabel {
    color: #f2f6fb;
    font-size: 12pt;
    font-weight: 700;
}

QLabel#StatusCaptionLabel {
    color: #91a4b8;
    font-size: 9.5pt;
}

QPushButton {
    min-height: 46px;
    padding: 10px 18px;
    border-radius: 12px;
    border: 1px solid #33495f;
    background-color: #182534;
    color: #f5f9fd;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #203147;
    border-color: #4a6682;
}

QPushButton:pressed {
    background-color: #0f1823;
}

QPushButton#PrimaryButton {
    background-color: #215884;
    border-color: #3b78a8;
}

QPushButton#PrimaryButton:hover {
    background-color: #2a6899;
}

QPushButton#DangerButton {
    background-color: #4b2530;
    border-color: #8b4b5c;
}

QPushButton#DangerButton:hover {
    background-color: #603240;
}

QMessageBox {
    background-color: #111b27;
}
"""


def apply_application_style(application: QApplication) -> None:
    """Uygulama genelinde karanlık mühendislik paneli görünümü uygular."""

    application.setStyle("Fusion")
    application.setStyleSheet(APPLICATION_STYLE_SHEET)
