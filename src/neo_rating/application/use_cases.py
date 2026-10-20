"""Application use cases."""

from __future__ import annotations

from neo_rating.application.ports import (
    Digest2ClassificationError,
    Digest2InitializationError,
    InputValidator,
    NeoClassifier,
    ScientificDataHashError,
    ScientificDataMissingError,
)
from neo_rating.domain.models import (
    CalculateNeoRatingRequest,
    CalculateNeoRatingResponse,
    InputProblem,
    ProblemSeverity,
    ResponseStatus,
)
from neo_rating.application.validation import normalize_mpc80_padding


class CalculateNeoRating:
    def __init__(self, classifier: NeoClassifier, validator: InputValidator) -> None:
        self._classifier = classifier
        self._validator = validator

    def execute(
        self, request: CalculateNeoRatingRequest
    ) -> CalculateNeoRatingResponse:
        if not request.source_text.strip():
            return self._failure(
                request,
                status=ResponseStatus.VALIDATION_ERROR,
                code="INPUT_EMPTY",
                message_key="error.input_empty",
            )

        source_text, padding_problems = normalize_mpc80_padding(request.source_text)
        try:
            problems = padding_problems + self._validator.validate(source_text)
        except Digest2InitializationError as exc:
            return self._failure(
                request,
                code="DIGEST2_INIT_FAILED",
                message_key="error.digest2_init_failed",
                details=str(exc),
            )
        if any(problem.severity is ProblemSeverity.ERROR for problem in problems):
            return CalculateNeoRatingResponse(
                status=ResponseStatus.VALIDATION_ERROR,
                ratings=(),
                problems=problems,
                scientific_identity=None,
                correlation_id=request.correlation_id,
            )

        try:
            ratings, identity = self._classifier.classify_text(source_text)
        except ScientificDataMissingError as exc:
            return self._failure(
                request,
                code="SCIENTIFIC_FILE_MISSING",
                message_key="error.scientific_file_missing",
                details=str(exc),
            )
        except ScientificDataHashError as exc:
            return self._failure(
                request,
                code="SCIENTIFIC_FILE_HASH",
                message_key="error.scientific_file_hash",
                details=str(exc),
            )
        except Digest2InitializationError as exc:
            return self._failure(
                request,
                code="DIGEST2_INIT_FAILED",
                message_key="error.digest2_init_failed",
                details=str(exc),
            )
        except Digest2ClassificationError as exc:
            return self._failure(
                request,
                code="DIGEST2_CLASSIFY_FAILED",
                message_key="error.digest2_classify_failed",
                details=str(exc),
            )
        except Exception:
            return self._failure(
                request,
                code="UNEXPECTED_FAILURE",
                message_key="error.unexpected_failure",
            )

        return CalculateNeoRatingResponse(
            status=ResponseStatus.SUCCESS,
            ratings=ratings,
            problems=problems,
            scientific_identity=identity,
            correlation_id=request.correlation_id,
        )

    @staticmethod
    def _failure(
        request: CalculateNeoRatingRequest,
        *,
        code: str,
        message_key: str,
        status: ResponseStatus = ResponseStatus.FAILURE,
        details: str | None = None,
    ) -> CalculateNeoRatingResponse:
        return CalculateNeoRatingResponse(
            status=status,
            ratings=(),
            problems=(
                InputProblem(
                    code=code,
                    severity=ProblemSeverity.ERROR,
                    message_key=message_key,
                    details=details,
                ),
            ),
            scientific_identity=None,
            correlation_id=request.correlation_id,
        )
