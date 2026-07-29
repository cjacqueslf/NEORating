from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from neo_rating.application.update_use_cases import CheckAndStageUpdate
from neo_rating.domain.updates import UpdateCandidate, UpdateStatus
from neo_rating.infrastructure.github_updates import (
    GitHubReleaseUpdateSource,
    VerifiedUpdateStager,
)


def _candidate(
    *,
    version: str = "0.2.0",
    payload: bytes = b"verified update",
) -> UpdateCandidate:
    return UpdateCandidate(
        version=version,
        digest2_version="2.8.2",
        asset_name="NEORating-0.2.0-win64.zip",
        asset_url=(
            "https://github.com/cjacqueslf/NEORating-Releases/"
            "releases/download/v0.2.0/NEORating-0.2.0-win64.zip"
        ),
        asset_sha256=hashlib.sha256(payload).hexdigest(),
        asset_size=len(payload),
    )


class FakeSource:
    def __init__(self, candidate: UpdateCandidate | None) -> None:
        self.candidate = candidate

    def latest_candidate(self) -> UpdateCandidate | None:
        return self.candidate


class FakeStager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.calls = 0

    def stage(self, candidate: UpdateCandidate) -> Path:
        self.calls += 1
        return self.path


def test_current_version_is_not_downloaded(tmp_path: Path) -> None:
    stager = FakeStager(tmp_path / "unused.zip")
    result = CheckAndStageUpdate(
        FakeSource(_candidate(version="0.1.0")),
        stager,
        current_version="0.1.0",
    ).execute()

    assert result.status is UpdateStatus.CURRENT
    assert stager.calls == 0


def test_newer_version_is_staged(tmp_path: Path) -> None:
    staged = tmp_path / "NEORating-0.2.0-win64.zip"
    result = CheckAndStageUpdate(
        FakeSource(_candidate()),
        FakeStager(staged),
        current_version="0.1.0",
    ).execute()

    assert result.status is UpdateStatus.STAGED
    assert result.version == "0.2.0"
    assert result.staged_path == staged


def test_network_failure_does_not_prevent_offline_startup(tmp_path: Path) -> None:
    class FailingSource:
        def latest_candidate(self):
            raise OSError("offline")

    result = CheckAndStageUpdate(
        FailingSource(),
        FakeStager(tmp_path / "unused.zip"),
        current_version="0.1.0",
    ).execute()

    assert result.status is UpdateStatus.UNAVAILABLE


def test_stager_rejects_wrong_hash(monkeypatch, tmp_path: Path) -> None:
    payload = b"tampered update"
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: io.BytesIO(payload),
    )

    with pytest.raises(ValueError, match="hash mismatch"):
        VerifiedUpdateStager(tmp_path).stage(_candidate(payload=b"expected update"))


def test_release_manifest_must_match_release_assets(monkeypatch) -> None:
    source = GitHubReleaseUpdateSource()
    payload = b"verified update"
    package_name = "NEORating-0.2.0-win64.zip"
    release = {
        "tag_name": "v0.2.0",
        "draft": False,
        "prerelease": False,
        "assets": [
            {
                "name": "neo-rating-update.json",
                "size": 200,
                "browser_download_url": (
                    "https://github.com/cjacqueslf/NEORating-Releases/"
                    "releases/download/v0.2.0/neo-rating-update.json"
                ),
            },
            {
                "name": package_name,
                "size": len(payload),
                "browser_download_url": (
                    "https://github.com/cjacqueslf/NEORating-Releases/"
                    f"releases/download/v0.2.0/{package_name}"
                ),
            },
        ],
    }
    manifest = {
        "schema_version": 1,
        "version": "0.2.0",
        "digest2_version": "2.8.2",
        "asset_name": package_name,
        "asset_size": len(payload),
        "asset_sha256": hashlib.sha256(payload).hexdigest(),
    }
    replies = iter((release, manifest))
    monkeypatch.setattr(source, "_read_json", lambda *args, **kwargs: next(replies))

    candidate = source.latest_candidate()

    assert candidate is not None
    assert candidate.version == "0.2.0"
    assert candidate.asset_name == package_name
