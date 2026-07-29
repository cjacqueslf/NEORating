"""Framework-independent domain values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    FAILURE = "failure"


class ProblemSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class InputProblem:
    code: str
    severity: ProblemSeverity
    message_key: str
    line_number: int | None = None
    details: str | None = None


@dataclass(frozen=True, slots=True)
class ScientificIdentity:
    application_version: str
    digest2_version: str
    model_sha256: str
    runtime_model_sha256: str
    config_sha256: str
    obscodes_sha256: str
    repeatable: bool


@dataclass(frozen=True, slots=True)
class TrackletRating:
    designation: str
    observation_count: int
    neo_rating: float
    raw_neo_score: float
    rms_arcsec: float
    rms_prime_arcsec: float
    top_noid_class: str
    noid_scores: Mapping[str, float]
    raw_scores: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "noid_scores", MappingProxyType(dict(self.noid_scores)))
        object.__setattr__(self, "raw_scores", MappingProxyType(dict(self.raw_scores)))


@dataclass(frozen=True, slots=True)
class CalculateNeoRatingRequest:
    source_text: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class CalculateNeoRatingResponse:
    status: ResponseStatus
    ratings: tuple[TrackletRating, ...]
    problems: tuple[InputProblem, ...]
    scientific_identity: ScientificIdentity | None
    correlation_id: str
