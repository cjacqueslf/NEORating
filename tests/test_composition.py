from __future__ import annotations

from pathlib import Path
import sys

from neo_rating.presentation.composition import _default_scientific_directory
from neo_rating.presentation.main import _verify_package


def test_frozen_application_resolves_bundled_scientific_data(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert _default_scientific_directory() == tmp_path / "resources" / "scientific"


def test_package_verification_executes_approved_digest2_sample() -> None:
    assert _verify_package() == 0
