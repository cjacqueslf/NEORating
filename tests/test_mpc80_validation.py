from __future__ import annotations

from neo_rating.application.validation import Mpc80EnvelopeValidator
from neo_rating.domain.models import ProblemSeverity
from neo_rating.infrastructure.digest2_adapter import Digest2Mpc80LineParser


def _validator() -> Mpc80EnvelopeValidator:
    return Mpc80EnvelopeValidator(Digest2Mpc80LineParser())


def _codes(text: str) -> list[str]:
    return [problem.code for problem in _validator().validate(text)]


def test_official_sample_has_no_problems(official_sample_text: str) -> None:
    assert _validator().validate(official_sample_text) == ()


def test_short_and_long_lines_are_rejected(official_sample_text: str) -> None:
    line = official_sample_text.splitlines()[0]

    assert "LINE_TOO_SHORT" in _codes(line[:-1])
    assert "LINE_TOO_LONG" in _codes(line + " ")


def test_non_ascii_line_is_rejected(official_sample_text: str) -> None:
    line = official_sample_text.splitlines()[0]
    changed = "ã" + line[1:]

    assert "LINE_NON_ASCII" in _codes(changed)


def test_invalid_fixed_fields_report_line_number(official_sample_text: str) -> None:
    first, second, third = official_sample_text.splitlines()
    invalid_ra = first[:32] + "99" + first[34:]
    invalid_dec = second[:44] + "?" + second[45:]
    invalid_obscode = third[:77] + "   "

    problems = _validator().validate(
        "\n".join((invalid_ra, invalid_dec, invalid_obscode))
    )

    assert ("LINE_FIELD_RA", 1) in [
        (problem.code, problem.line_number) for problem in problems
    ]
    assert ("LINE_FIELD_DEC", 2) in [
        (problem.code, problem.line_number) for problem in problems
    ]
    assert ("LINE_FIELD_OBSCODE", 3) in [
        (problem.code, problem.line_number) for problem in problems
    ]


def test_invalid_date_and_magnitude_are_rejected(
    official_sample_text: str,
) -> None:
    first, second, third = official_sample_text.splitlines()
    invalid_date = first[:20] + "13" + first[22:]
    invalid_magnitude = second[:65] + "XX.XX" + second[70:]

    codes = _codes("\n".join((invalid_date, invalid_magnitude, third)))

    assert "LINE_FIELD_DATE" in codes
    assert "LINE_FIELD_MAGNITUDE" in codes


def test_single_observation_tracklet_is_rejected(official_sample_text: str) -> None:
    problem_codes = _codes(official_sample_text.splitlines()[0])

    assert "TRACKLET_TOO_SHORT" in problem_codes


def test_time_must_not_move_backwards(official_sample_text: str) -> None:
    lines = official_sample_text.splitlines()

    problems = _validator().validate("\n".join(reversed(lines)))

    assert any(
        problem.code == "TRACKLET_TIME_ORDER" and problem.line_number == 2
        for problem in problems
    )


def test_blank_line_is_a_non_blocking_warning(official_sample_text: str) -> None:
    text = official_sample_text.splitlines()[0] + "\n\n" + "\n".join(
        official_sample_text.splitlines()[1:]
    )

    problems = _validator().validate(text)

    assert len(problems) == 1
    assert problems[0].code == "LINE_EMPTY"
    assert problems[0].line_number == 2
    assert problems[0].severity is ProblemSeverity.WARNING


def test_two_designations_are_grouped_independently(
    official_sample_text: str,
) -> None:
    lines = official_sample_text.splitlines()
    second_tracklet = [
        line[:5] + "K16S98A" + line[12:]
        for line in lines[:2]
    ]

    assert _validator().validate("\n".join(lines + second_tracklet)) == ()


def test_orphan_auxiliary_line_is_rejected(official_sample_text: str) -> None:
    line = official_sample_text.splitlines()[0]
    auxiliary = line[:14] + "s" + line[15:]

    assert "ORPHAN_AUXILIARY_LINE" in _codes(auxiliary)


def _satellite_pair(main_line: str) -> tuple[str, str]:
    main = main_line[:14] + "S" + main_line[15:]
    auxiliary = [" "] * 80
    auxiliary[:12] = main[:12]
    auxiliary[14] = "s"
    auxiliary[32] = "2"
    auxiliary[34:45] = f"{0.0001:11.7f}"
    auxiliary[46:57] = f"{0.0002:11.7f}"
    auxiliary[58:69] = f"{0.0003:11.7f}"
    auxiliary[77:80] = main[77:80]
    return main, "".join(auxiliary)


def test_valid_satellite_auxiliary_line_is_accepted(
    official_sample_text: str,
) -> None:
    lines = official_sample_text.splitlines()
    main, auxiliary = _satellite_pair(lines[0])

    assert _validator().validate("\n".join((main, auxiliary, *lines[1:]))) == ()


def test_malformed_satellite_auxiliary_line_is_rejected(
    official_sample_text: str,
) -> None:
    lines = official_sample_text.splitlines()
    main, auxiliary = _satellite_pair(lines[0])
    malformed = auxiliary[:34] + "not-a-num  " + auxiliary[45:]

    assert "AUXILIARY_PARSE_FAILED" in _codes(
        "\n".join((main, malformed, *lines[1:]))
    )
