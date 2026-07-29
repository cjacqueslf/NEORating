"""Resolution and verification of approved scientific resources."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from neo_rating.application.ports import (
    ScientificDataHashError,
    ScientificDataMissingError,
)


@dataclass(frozen=True, slots=True)
class VerifiedScientificData:
    digest2_version: str
    model_path: Path
    runtime_model_path: Path
    config_path: Path
    obscodes_path: Path
    model_sha256: str
    runtime_model_sha256: str
    config_sha256: str
    obscodes_sha256: str
    repeatable: bool


class ScientificDataBundle:
    def __init__(self, directory: Path) -> None:
        self._directory = directory.resolve()

    def verify(self) -> VerifiedScientificData:
        manifest_path = self._directory / "manifest.json"
        if not manifest_path.is_file():
            raise ScientificDataMissingError("manifest.json")

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ScientificDataHashError("manifest.json is unreadable") from exc

        approved_files = manifest.get("files")
        if not isinstance(approved_files, dict):
            raise ScientificDataHashError("manifest.json has no files mapping")

        verified: dict[str, tuple[Path, str]] = {}
        for filename in (
            "digest2.model.csv",
            "digest2.model",
            "MPC.config",
            "digest2.obscodes",
        ):
            path = self._directory / filename
            if not path.is_file():
                raise ScientificDataMissingError(filename)

            entry = approved_files.get(filename)
            expected = entry.get("sha256") if isinstance(entry, dict) else None
            if not isinstance(expected, str):
                raise ScientificDataHashError(f"{filename}: missing approved SHA-256")

            actual = _sha256(path)
            if actual.lower() != expected.lower():
                raise ScientificDataHashError(
                    f"{filename}: expected {expected.lower()}, got {actual}"
                )
            verified[filename] = (path, actual)

        model_path, model_hash = verified["digest2.model.csv"]
        runtime_model_path, runtime_model_hash = verified["digest2.model"]
        config_path, config_hash = verified["MPC.config"]
        obscodes_path, obscodes_hash = verified["digest2.obscodes"]
        return VerifiedScientificData(
            digest2_version=str(manifest["digest2_version"]),
            model_path=model_path,
            runtime_model_path=runtime_model_path,
            config_path=config_path,
            obscodes_path=obscodes_path,
            model_sha256=model_hash,
            runtime_model_sha256=runtime_model_hash,
            config_sha256=config_hash,
            obscodes_sha256=obscodes_hash,
            repeatable=bool(manifest.get("repeatable", True)),
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
