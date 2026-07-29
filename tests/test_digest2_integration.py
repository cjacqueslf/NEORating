from __future__ import annotations

import socket
import urllib.request

from neo_rating.infrastructure.digest2_adapter import (
    Digest2Classifier,
    Digest2Mpc80LineParser,
)


def test_official_sample_returns_approved_scores(
    scientific_data, official_sample_text
) -> None:
    ratings, identity = Digest2Classifier(scientific_data).classify_text(
        official_sample_text
    )

    assert len(ratings) == 1
    rating = ratings[0]
    assert rating.designation == "K16S99K"
    assert rating.observation_count == 3
    assert rating.neo_rating == 20.03939848070969
    assert rating.raw_neo_score == 10.564506231433699
    assert rating.rms_arcsec == 0.7306750322258272
    assert rating.top_noid_class == "MB1"
    assert identity.digest2_version == "2.8.1"
    assert identity.repeatable is True


def test_repeatable_mode_returns_identical_results(
    scientific_data, official_sample_text
) -> None:
    classifier = Digest2Classifier(scientific_data)

    first = classifier.classify_text(official_sample_text)
    second = classifier.classify_text(official_sample_text)

    assert first == second


def test_explicit_local_data_does_not_access_network(
    monkeypatch, scientific_data, official_sample_text
) -> None:
    def fail_network(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    monkeypatch.setattr(socket, "create_connection", fail_network)

    ratings, _ = Digest2Classifier(scientific_data).classify_text(
        official_sample_text
    )

    assert ratings[0].neo_rating == 20.03939848070969


def test_official_line_parser_accepts_exact_80_columns(
    official_sample_text,
) -> None:
    line = official_sample_text.splitlines()[0]

    assert len(line) == 80
    assert Digest2Mpc80LineParser().accepts_main_line(line) is True


def test_source_text_is_not_modified(
    scientific_data, official_sample_text
) -> None:
    original = official_sample_text

    Digest2Classifier(scientific_data).classify_text(original)

    assert official_sample_text == original


def test_multiple_tracklets_preserve_first_appearance_order(
    scientific_data, official_sample_text
) -> None:
    lines = official_sample_text.splitlines()
    second_tracklet = [
        line[:5] + "K16S98A" + line[12:]
        for line in lines[:2]
    ]
    source = "\n".join((*lines, *second_tracklet))

    ratings, _ = Digest2Classifier(scientific_data).classify_text(source)

    assert [rating.designation for rating in ratings] == ["K16S99K", "K16S98A"]
    assert [rating.observation_count for rating in ratings] == [3, 2]
