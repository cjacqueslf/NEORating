"""Structural validation for pasted MPC 80-column observations."""

from __future__ import annotations

import calendar
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from neo_rating.application.ports import Mpc80LineParser
from neo_rating.domain.models import InputProblem, ProblemSeverity


_MAIN_TYPES = frozenset(("C", "S", "B"))
_AUXILIARY_TYPES = frozenset(("s", "v"))


@dataclass(slots=True)
class _TrackletState:
    first_line: int
    observation_count: int = 0
    last_time: tuple[int, int, Decimal] | None = None


class Mpc80EnvelopeValidator:
    """Validate the MPC80 envelope while leaving scientific parsing to Digest2."""

    def __init__(self, official_parser: Mpc80LineParser) -> None:
        self._official_parser = official_parser

    def validate(self, source_text: str) -> tuple[InputProblem, ...]:
        problems: list[InputProblem] = []
        tracklets: OrderedDict[str, _TrackletState] = OrderedDict()
        last_main_designation: str | None = None
        last_main_line: str | None = None

        for line_number, line in enumerate(source_text.splitlines(), start=1):
            if not line.strip():
                problems.append(
                    _problem(
                        "LINE_EMPTY",
                        "warning.line_empty",
                        line_number,
                        severity=ProblemSeverity.WARNING,
                    )
                )
                continue

            if len(line) < 80:
                problems.append(
                    _problem("LINE_TOO_SHORT", "error.line_too_short", line_number)
                )
                last_main_designation = None
                last_main_line = None
                continue
            if len(line) > 80:
                problems.append(
                    _problem("LINE_TOO_LONG", "error.line_too_long", line_number)
                )
                last_main_designation = None
                last_main_line = None
                continue
            try:
                line.encode("ascii")
            except UnicodeEncodeError:
                problems.append(
                    _problem("LINE_NON_ASCII", "error.line_non_ascii", line_number)
                )
                last_main_designation = None
                last_main_line = None
                continue

            designation = line[:12]
            if not designation.strip():
                problems.append(
                    _problem(
                        "LINE_FIELD_DESIGNATION",
                        "error.line_field_designation",
                        line_number,
                    )
                )
                last_main_designation = None
                last_main_line = None
                continue

            observation_type = line[14]
            if observation_type in _AUXILIARY_TYPES:
                if last_main_designation != designation or last_main_line is None:
                    problems.append(
                        _problem(
                            "ORPHAN_AUXILIARY_LINE",
                            "error.orphan_auxiliary_line",
                            line_number,
                        )
                    )
                elif not self._official_parser.accepts_auxiliary_pair(
                    last_main_line, line
                ):
                    problems.append(
                        _problem(
                            "AUXILIARY_PARSE_FAILED",
                            "error.auxiliary_parse_failed",
                            line_number,
                        )
                    )
                continue

            if observation_type not in _MAIN_TYPES:
                problems.append(
                    _problem(
                        "LINE_UNSUPPORTED",
                        "error.line_unsupported",
                        line_number,
                    )
                )
                last_main_designation = None
                last_main_line = None
                continue

            line_problems, time_key = _validate_main_fields(line, line_number)
            problems.extend(line_problems)
            if line_problems:
                last_main_designation = None
                last_main_line = None
                continue

            if not self._official_parser.accepts_main_line(line):
                problems.append(
                    _problem(
                        "LINE_PARSE_FAILED",
                        "error.line_parse_failed",
                        line_number,
                    )
                )
                last_main_designation = None
                last_main_line = None
                continue

            state = tracklets.setdefault(
                designation, _TrackletState(first_line=line_number)
            )
            if state.last_time is not None and time_key < state.last_time:
                problems.append(
                    _problem(
                        "TRACKLET_TIME_ORDER",
                        "error.tracklet_time_order",
                        line_number,
                    )
                )
            state.observation_count += 1
            state.last_time = time_key
            last_main_designation = designation
            last_main_line = line

        for state in tracklets.values():
            if state.observation_count < 2:
                problems.append(
                    _problem(
                        "TRACKLET_TOO_SHORT",
                        "error.tracklet_too_short",
                        state.first_line,
                    )
                )

        return tuple(problems)


def _validate_main_fields(
    line: str, line_number: int
) -> tuple[list[InputProblem], tuple[int, int, Decimal]]:
    problems: list[InputProblem] = []
    time_key = (0, 0, Decimal(0))

    try:
        year = int(line[15:19])
        month = int(line[20:22])
        day = Decimal(line[23:32].strip())
        whole_day = int(day)
        if not 1 <= month <= 12:
            raise ValueError
        if day < 1 or day >= Decimal(calendar.monthrange(year, month)[1] + 1):
            raise ValueError
        if whole_day < 1:
            raise ValueError
        time_key = (year, month, day)
    except (ValueError, InvalidOperation, OverflowError):
        problems.append(
            _problem("LINE_FIELD_DATE", "error.line_field_date", line_number)
        )

    try:
        hour = int(line[32:34])
        minute = int(line[35:37])
        second = Decimal(line[38:44].strip())
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second < 60):
            raise ValueError
    except (ValueError, InvalidOperation, OverflowError):
        problems.append(_problem("LINE_FIELD_RA", "error.line_field_ra", line_number))

    try:
        sign = line[44]
        degree = int(line[45:47])
        minute = int(line[48:50])
        second = Decimal(line[51:56].strip())
        if sign not in ("+", "-"):
            raise ValueError
        if not (0 <= degree <= 90 and 0 <= minute <= 59 and 0 <= second < 60):
            raise ValueError
        if degree == 90 and (minute != 0 or second != 0):
            raise ValueError
    except (ValueError, InvalidOperation, OverflowError):
        problems.append(
            _problem("LINE_FIELD_DEC", "error.line_field_dec", line_number)
        )

    magnitude = line[65:70].strip()
    if magnitude:
        try:
            parsed_magnitude = Decimal(magnitude)
            if not parsed_magnitude.is_finite():
                raise InvalidOperation
        except InvalidOperation:
            problems.append(
                _problem(
                    "LINE_FIELD_MAGNITUDE",
                    "error.line_field_magnitude",
                    line_number,
                )
            )

    if not line[77:80].strip():
        problems.append(
            _problem(
                "LINE_FIELD_OBSCODE",
                "error.line_field_obscode",
                line_number,
            )
        )

    return problems, time_key


def _problem(
    code: str,
    message_key: str,
    line_number: int,
    *,
    severity: ProblemSeverity = ProblemSeverity.ERROR,
) -> InputProblem:
    return InputProblem(
        code=code,
        severity=severity,
        message_key=message_key,
        line_number=line_number,
    )
