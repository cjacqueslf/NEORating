"""Application composition without global service locators."""

from __future__ import annotations

from pathlib import Path

from neo_rating.application.use_cases import CalculateNeoRating
from neo_rating.application.validation import Mpc80EnvelopeValidator
from neo_rating.infrastructure.digest2_adapter import (
    Digest2Classifier,
    Digest2Mpc80LineParser,
)
from neo_rating.infrastructure.scientific_data import ScientificDataBundle


def build_calculate_neo_rating(
    scientific_directory: Path | None = None,
) -> CalculateNeoRating:
    directory = scientific_directory or _default_scientific_directory()
    classifier = Digest2Classifier(ScientificDataBundle(directory))
    validator = Mpc80EnvelopeValidator(Digest2Mpc80LineParser())
    return CalculateNeoRating(classifier, validator)


def _default_scientific_directory() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "resources" / "scientific"

