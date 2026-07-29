from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from neo_rating.infrastructure.scientific_data import ScientificDataBundle


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scientific_data() -> ScientificDataBundle:
    return ScientificDataBundle(PROJECT_ROOT / "resources" / "scientific")


@pytest.fixture
def official_sample_text() -> str:
    return "\n".join(
        (
            "     K16S99K 1C2022 12 25.38496508 32 36.283+17 10 35.94         21.98GV     G96",
            "     K16S99K 1C2022 12 25.39527308 32 35.635+17 10 37.27         21.72GV     G96",
            "     K16S99K 1C2022 12 25.40040208 32 35.473+17 10 37.38         21.31GV     G96",
        )
    )


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
