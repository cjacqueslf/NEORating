from __future__ import annotations

from neo_rating.application.use_cases import CalculateNeoRating
from neo_rating.domain.models import (
    CalculateNeoRatingRequest,
    InputProblem,
    ProblemSeverity,
    ResponseStatus,
    ScientificIdentity,
)


class FakeClassifier:
    def classify_text(self, source_text: str):
        return (), ScientificIdentity(
            application_version="0.1.0",
            digest2_version="2.8.1",
            model_sha256="a",
            runtime_model_sha256="runtime-a",
            config_sha256="b",
            obscodes_sha256="c",
            repeatable=True,
        )


class NoProblemsValidator:
    def validate(self, source_text: str):
        return ()


class BlockingValidator:
    def validate(self, source_text: str):
        return (
            InputProblem(
                code="LINE_TOO_SHORT",
                severity=ProblemSeverity.ERROR,
                message_key="error.line_too_short",
                line_number=1,
            ),
        )


class MustNotRunClassifier:
    def classify_text(self, source_text: str):
        raise AssertionError("classifier must not run")


def test_empty_input_is_rejected_without_calling_classifier() -> None:
    response = CalculateNeoRating(FakeClassifier(), NoProblemsValidator()).execute(
        CalculateNeoRatingRequest(source_text=" \n", correlation_id="test-1")
    )

    assert response.status is ResponseStatus.VALIDATION_ERROR
    assert response.problems[0].code == "INPUT_EMPTY"
    assert response.correlation_id == "test-1"


def test_success_preserves_correlation_id() -> None:
    response = CalculateNeoRating(FakeClassifier(), NoProblemsValidator()).execute(
        CalculateNeoRatingRequest(source_text="content", correlation_id="test-2")
    )

    assert response.status is ResponseStatus.SUCCESS
    assert response.scientific_identity is not None
    assert response.correlation_id == "test-2"


def test_validation_error_blocks_scientific_classifier() -> None:
    response = CalculateNeoRating(
        MustNotRunClassifier(), BlockingValidator()
    ).execute(
        CalculateNeoRatingRequest(source_text="invalid", correlation_id="test-3")
    )

    assert response.status is ResponseStatus.VALIDATION_ERROR
    assert response.problems[0].line_number == 1
