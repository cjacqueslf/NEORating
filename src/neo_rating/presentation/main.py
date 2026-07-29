"""Desktop entry point."""

from __future__ import annotations

from math import isclose
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from neo_rating.presentation.composition import (
    build_calculate_neo_rating,
    build_update_service,
)
from neo_rating.presentation.main_window import MainWindow
from neo_rating.domain.models import CalculateNeoRatingRequest, ResponseStatus


_PACKAGE_VERIFICATION_SAMPLE = "\n".join(
    (
        "     K16S99K 1C2022 12 25.38496508 32 36.283+17 10 35.94         21.98GV     G96",
        "     K16S99K 1C2022 12 25.39527308 32 35.635+17 10 37.27         21.72GV     G96",
        "     K16S99K 1C2022 12 25.40040208 32 35.473+17 10 37.38         21.31GV     G96",
    )
)


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
    if "--verify-package" in sys.argv[1:]:
        return _verify_package()

    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("NEO Rating")
    application.setOrganizationName("NEO Rating")
    application.setStyle("Fusion")
    _apply_dark_palette(application)

    window = MainWindow(
        build_calculate_neo_rating(),
        update_use_case=build_update_service(),
    )
    window.show()
    return application.exec()


def _verify_package() -> int:
    response = build_calculate_neo_rating().execute(
        CalculateNeoRatingRequest(
            source_text=_PACKAGE_VERIFICATION_SAMPLE,
            correlation_id="package-verification",
        )
    )
    if response.status is not ResponseStatus.SUCCESS or len(response.ratings) != 1:
        return 2
    rating = response.ratings[0]
    if rating.designation != "K16S99K":
        return 3
    if not isclose(rating.neo_rating, 20.03939848070969, abs_tol=1e-12):
        return 4
    identity = response.scientific_identity
    if identity is None or identity.digest2_version != "2.8.1":
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
