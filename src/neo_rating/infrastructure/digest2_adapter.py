"""Adapter for the official MPC Digest2 Python package."""

from __future__ import annotations

from collections import OrderedDict
from importlib.metadata import PackageNotFoundError, version
from operator import attrgetter
from pathlib import Path
from tempfile import NamedTemporaryFile

from neo_rating import __version__
from neo_rating.application.ports import (
    Digest2ClassificationError,
    Digest2InitializationError,
)
from neo_rating.domain.models import ScientificIdentity, TrackletRating
from neo_rating.infrastructure.scientific_data import ScientificDataBundle


class Digest2Classifier:
    def __init__(self, scientific_data: ScientificDataBundle) -> None:
        self._scientific_data = scientific_data

    def classify_text(
        self, source_text: str
    ) -> tuple[tuple[TrackletRating, ...], ScientificIdentity]:
        data = self._scientific_data.verify()
        installed_version = _installed_digest2_version()
        if installed_version != data.digest2_version:
            raise Digest2InitializationError(
                f"Digest2 {data.digest2_version} required; {installed_version} installed"
            )

        try:
            from digest2 import Digest2, parse_mpc80_file
        except ImportError as exc:
            raise Digest2InitializationError("Digest2 package is unavailable") from exc

        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="ascii",
                newline="\n",
                suffix=".obs",
                delete=False,
            ) as temporary:
                temporary.write(source_text)
                if source_text and not source_text.endswith(("\n", "\r")):
                    temporary.write("\n")
                temporary_path = Path(temporary.name)
            parsed = parse_mpc80_file(str(temporary_path))
            tracklets: OrderedDict[str, list[object]] = OrderedDict(parsed.items())
            for observations in tracklets.values():
                observations.sort(key=attrgetter("mjd"))
        except Exception as exc:
            raise Digest2ClassificationError("MPC80 parsing failed") from exc
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        if not tracklets:
            raise Digest2ClassificationError("No MPC80 tracklet was accepted")
        if any(len(observations) < 2 for observations in tracklets.values()):
            raise Digest2ClassificationError(
                "Every accepted tracklet requires at least two observations"
            )

        try:
            with Digest2(
                model_path=str(data.model_path),
                config_path=str(data.config_path),
                obscodes_path=str(data.obscodes_path),
                repeatable=data.repeatable,
                no_threshold=False,
            ) as classifier:
                ratings = tuple(
                    _to_rating(
                        designation=designation,
                        observations=observations,
                        result=classifier.classify_tracklet(
                            observations,
                            collect_orbits=False,
                        ),
                    )
                    for designation, observations in tracklets.items()
                )
        except Exception as exc:
            raise Digest2ClassificationError("Digest2 classification failed") from exc

        identity = ScientificIdentity(
            application_version=__version__,
            digest2_version=installed_version,
            model_sha256=data.model_sha256,
            runtime_model_sha256=data.runtime_model_sha256,
            config_sha256=data.config_sha256,
            obscodes_sha256=data.obscodes_sha256,
            repeatable=data.repeatable,
        )
        return ratings, identity


class Digest2Mpc80LineParser:
    """Thin access to the official parser for validation."""

    def accepts_main_line(self, line: str) -> bool:
        try:
            from digest2 import parse_mpc80
        except ImportError as exc:
            raise Digest2InitializationError("Digest2 package is unavailable") from exc
        return parse_mpc80(line) is not None

    def accepts_auxiliary_pair(self, main_line: str, auxiliary_line: str) -> bool:
        try:
            from digest2 import parse_mpc80_file
        except ImportError as exc:
            raise Digest2InitializationError("Digest2 package is unavailable") from exc

        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="ascii",
                newline="\n",
                suffix=".obs",
                delete=False,
            ) as temporary:
                temporary.write(main_line)
                temporary.write("\n")
                temporary.write(auxiliary_line)
                temporary.write("\n")
                temporary_path = Path(temporary.name)
            parsed = parse_mpc80_file(str(temporary_path))
            observations = parsed.get(main_line[:12], [])
            return len(observations) == 1 and observations[0].spacebased is True
        except (OSError, UnicodeError):
            return False
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def _installed_digest2_version() -> str:
    try:
        return version("digest2")
    except PackageNotFoundError as exc:
        raise Digest2InitializationError("Digest2 package is unavailable") from exc


def _to_rating(*, designation: str, observations: list[object], result: object) -> TrackletRating:
    noid_scores = dict(result.noid.items())
    raw_scores = dict(result.raw.items())
    return TrackletRating(
        designation=designation.strip(),
        observation_count=len(observations),
        neo_rating=result.noid.NEO,
        raw_neo_score=result.raw.NEO,
        rms_arcsec=result.rms,
        rms_prime_arcsec=result.rms_prime,
        top_noid_class=result.top_class,
        noid_scores=noid_scores,
        raw_scores=raw_scores,
    )
