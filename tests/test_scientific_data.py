from __future__ import annotations

import json
from pathlib import Path

import pytest

from neo_rating.application.ports import ScientificDataHashError
from neo_rating.infrastructure.scientific_data import ScientificDataBundle


def test_approved_scientific_bundle_is_verified(scientific_data) -> None:
    verified = scientific_data.verify()

    assert verified.digest2_version == "2.8.1"
    assert verified.repeatable is True
    assert verified.model_sha256 == (
        "2b9d9d2a6d8ab16d3a2dbb835b30d3aa172431f27c3cb7c159675d7686668c45"
    )
    assert verified.runtime_model_sha256 == (
        "77a7ce32d15f6e363d5dca03bba87916302c29f76d499ca4e70f655a2356e9f8"
    )


def test_modified_scientific_file_is_rejected(
    tmp_path: Path, scientific_data: ScientificDataBundle
) -> None:
    original = scientific_data.verify()
    (tmp_path / "digest2.model.csv").write_bytes(original.model_path.read_bytes())
    (tmp_path / "digest2.model").write_bytes(original.runtime_model_path.read_bytes())
    (tmp_path / "MPC.config").write_bytes(original.config_path.read_bytes() + b"\n")
    (tmp_path / "digest2.obscodes").write_bytes(original.obscodes_path.read_bytes())
    manifest = {
        "digest2_version": "2.8.1",
        "repeatable": True,
        "files": {
            "digest2.model.csv": {"sha256": original.model_sha256},
            "digest2.model": {"sha256": original.runtime_model_sha256},
            "MPC.config": {"sha256": original.config_sha256},
            "digest2.obscodes": {"sha256": original.obscodes_sha256},
        },
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ScientificDataHashError):
        ScientificDataBundle(tmp_path).verify()
