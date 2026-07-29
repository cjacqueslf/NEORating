"""Desktop entry point."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from neo_rating.presentation.composition import build_calculate_neo_rating
from neo_rating.presentation.main_window import MainWindow


def _apply_dark_palette(application: QApplication) -> None:
    application.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121820"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e8edf3"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0b1016"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#141d26"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#263443"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f4f7fa"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e2e8ef"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#25313e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e8edf3"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1479cc"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#718091"))
    application.setPalette(palette)


def main() -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("NEO Rating")
    application.setOrganizationName("NEO Rating")
    application.setStyle("Fusion")
    _apply_dark_palette(application)

    window = MainWindow(build_calculate_neo_rating())
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
