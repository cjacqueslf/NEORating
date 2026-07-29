"""Controlled update discovery and staging through GitHub Releases."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from neo_rating.domain.updates import UpdateCandidate

RELEASE_API_URL = (
    "https://api.github.com/repos/cjacqueslf/NEORating-Releases/releases/latest"
)
UPDATE_MANIFEST_NAME = "neo-rating-update.json"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_PACKAGE_BYTES = 512 * 1024 * 1024


class GitHubReleaseUpdateSource:
    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self._timeout_seconds = timeout_seconds

    def latest_candidate(self) -> UpdateCandidate | None:
        try:
            release = self._read_json(RELEASE_API_URL, MAX_MANIFEST_BYTES)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        if release.get("draft") or release.get("prerelease"):
            return None
        assets = _assets_by_name(release)
        manifest_asset = assets.get(UPDATE_MANIFEST_NAME)
        if manifest_asset is None:
            return None
        manifest = self._read_json(
            _asset_url(manifest_asset),
            MAX_MANIFEST_BYTES,
            accept="application/octet-stream",
        )
        if manifest.get("schema_version") != 1:
            raise ValueError("unsupported update manifest")
        asset_name = _required_string(manifest, "asset_name")
        package_asset = assets.get(asset_name)
        if package_asset is None:
            raise ValueError("release package is missing")
        version = _required_string(manifest, "version")
        if release.get("tag_name") not in {version, f"v{version}"}:
            raise ValueError("release tag and manifest version differ")
        expected_size = _required_positive_int(manifest, "asset_size")
        actual_size = package_asset.get("size")
        if actual_size != expected_size or expected_size > MAX_PACKAGE_BYTES:
            raise ValueError("release package size differs from manifest")
        sha256 = _required_string(manifest, "asset_sha256").lower()
        if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
            raise ValueError("invalid SHA-256")
        return UpdateCandidate(
            version=version,
            digest2_version=_required_string(manifest, "digest2_version"),
            asset_name=asset_name,
            asset_url=_asset_url(package_asset),
            asset_sha256=sha256,
            asset_size=expected_size,
        )

    def _read_json(
        self,
        url: str,
        maximum_bytes: int,
        *,
        accept: str = "application/vnd.github+json",
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": accept,
                "User-Agent": "NEORating-Updater",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            payload = response.read(maximum_bytes + 1)
        if len(payload) > maximum_bytes:
            raise ValueError("update metadata is too large")
        parsed = json.loads(payload.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("update metadata is not an object")
        return parsed


class VerifiedUpdateStager:
    def __init__(self, directory: Path, *, timeout_seconds: float = 30.0) -> None:
        self._directory = directory.resolve()
        self._timeout_seconds = timeout_seconds

    def stage(self, candidate: UpdateCandidate) -> Path:
        if Path(candidate.asset_name).name != candidate.asset_name:
            raise ValueError("unsafe update asset name")
        version_directory = self._directory / candidate.version
        version_directory.mkdir(parents=True, exist_ok=True)
        destination = version_directory / candidate.asset_name
        if destination.is_file() and _sha256(destination) == candidate.asset_sha256:
            return destination

        descriptor, temporary_name = tempfile.mkstemp(
            prefix="neo-rating-",
            suffix=".download",
            dir=version_directory,
        )
        temporary_path = Path(temporary_name)
        try:
            digest = hashlib.sha256()
            total = 0
            request = urllib.request.Request(
                candidate.asset_url,
                headers={
                    "Accept": "application/octet-stream",
                    "User-Agent": "NEORating-Updater",
                },
            )
            with os.fdopen(descriptor, "wb") as output:
                with urllib.request.urlopen(
                    request, timeout=self._timeout_seconds
                ) as response:
                    while block := response.read(1024 * 1024):
                        total += len(block)
                        if total > candidate.asset_size:
                            raise ValueError("update package exceeds approved size")
                        digest.update(block)
                        output.write(block)
                output.flush()
                os.fsync(output.fileno())
            if total != candidate.asset_size:
                raise ValueError("update package size mismatch")
            if digest.hexdigest() != candidate.asset_sha256:
                raise ValueError("update package hash mismatch")
            os.replace(temporary_path, destination)
            return destination
        finally:
            temporary_path.unlink(missing_ok=True)


def default_update_directory() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return base / "NEORating" / "updates"


def _assets_by_name(release: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError("release has no assets")
    result: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if isinstance(asset, dict) and isinstance(asset.get("name"), str):
            result[asset["name"]] = asset
    return result


def _asset_url(asset: dict[str, Any]) -> str:
    url = _required_string(asset, "browser_download_url")
    if not url.startswith("https://github.com/"):
        raise ValueError("update asset is not hosted by GitHub")
    return url


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing {key}")
    return value


def _required_positive_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"invalid {key}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
