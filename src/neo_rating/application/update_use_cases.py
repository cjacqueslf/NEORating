"""Application orchestration for controlled automatic updates."""

from __future__ import annotations

from pathlib import Path

from neo_rating.application.ports import UpdateSource, UpdateStager
from neo_rating.domain.updates import UpdateResult, UpdateStatus


class CheckAndStageUpdate:
    def __init__(
        self,
        source: UpdateSource,
        stager: UpdateStager,
        *,
        current_version: str,
    ) -> None:
        self._source = source
        self._stager = stager
        self._current_version = current_version

    def execute(self) -> UpdateResult:
        try:
            candidate = self._source.latest_candidate()
            if candidate is None or not _is_newer(
                candidate.version, self._current_version
            ):
                return UpdateResult(status=UpdateStatus.CURRENT)
            staged_path = self._stager.stage(candidate)
            if not isinstance(staged_path, Path):
                raise TypeError("update stager returned an invalid path")
            return UpdateResult(
                status=UpdateStatus.STAGED,
                version=candidate.version,
                staged_path=staged_path,
            )
        except (OSError, ValueError, TypeError):
            return UpdateResult(
                status=UpdateStatus.UNAVAILABLE,
                technical_code="UPDATE_CHECK_UNAVAILABLE",
            )


def _is_newer(candidate: str, current: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def _version_tuple(value: str) -> tuple[int, int, int]:
    normalized = value.removeprefix("v")
    parts = normalized.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("version is not strict semantic version")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]
