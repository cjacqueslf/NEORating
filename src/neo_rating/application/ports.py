"""Ports implemented by infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from neo_rating.domain.models import InputProblem, ScientificIdentity, TrackletRating
from neo_rating.domain.updates import UpdateCandidate


class ClassificationError(RuntimeError):
    """Base error raised by a scientific classifier adapter."""


class ScientificDataMissingError(ClassificationError):
    """A required scientific resource is absent."""


class ScientificDataHashError(ClassificationError):
    """A scientific resource differs from the approved manifest."""


class Digest2InitializationError(ClassificationError):
    """The official Digest2 engine could not be initialized."""


class Digest2ClassificationError(ClassificationError):
    """The official Digest2 engine could not classify the input."""


class NeoClassifier(Protocol):
    def classify_text(
        self, source_text: str
    ) -> tuple[tuple[TrackletRating, ...], ScientificIdentity]:
        """Classify MPC80 text without changing its contents."""


class Mpc80LineParser(Protocol):
    def accepts_main_line(self, line: str) -> bool:
        """Return whether the official Digest2 parser accepts one main line."""

    def accepts_auxiliary_pair(self, main_line: str, auxiliary_line: str) -> bool:
        """Return whether Digest2 applies an auxiliary line to its main line."""


class InputValidator(Protocol):
    def validate(self, source_text: str) -> tuple[InputProblem, ...]:
        """Return every problem found without changing the source."""


class UpdateSource(Protocol):
    def latest_candidate(self) -> UpdateCandidate | None:
        """Return the latest approved release candidate, if one exists."""


class UpdateStager(Protocol):
    def stage(self, candidate: UpdateCandidate) -> Path:
        """Download and atomically stage a verified release asset."""
