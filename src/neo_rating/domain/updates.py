"""Framework-independent update values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class UpdateStatus(StrEnum):
    CURRENT = "current"
    STAGED = "staged"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class UpdateCandidate:
    version: str
    digest2_version: str
    asset_name: str
    asset_url: str
    asset_sha256: str
    asset_size: int


@dataclass(frozen=True, slots=True)
class UpdateResult:
    status: UpdateStatus
    version: str | None = None
    staged_path: Path | None = None
    technical_code: str | None = None
