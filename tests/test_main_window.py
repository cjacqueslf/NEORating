from __future__ import annotations

import threading
from types import MappingProxyType

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtTest import QTest

from neo_rating.domain.models import (
    CalculateNeoRatingResponse,
    InputProblem,
    ProblemSeverity,
    ResponseStatus,
    ScientificIdentity,
    TrackletRating,
)
from neo_rating.presentation.main_window import MainWindow, WindowState


def _identity() -> ScientificIdentity:
    return ScientificIdentity(
        application_version="0.1.0",
        digest2_version="2.8.1",
        model_sha256="model",
        runtime_model_sha256="runtime",
        config_sha256="config",
        obscodes_sha256="obscodes",
        repeatable=True,
    )


def _rating() -> TrackletRating:
    return TrackletRating(
        designation="K16S99K",
        observation_count=3,
        neo_rating=20.03939848070969,
        raw_neo_score=10.564506231433699,
        rms_arcsec=0.7306750322258272,
        rms_prime_arcsec=0.0,
        top_noid_class="MB1",
        noid_scores=MappingProxyType({"NEO": 20.03939848070969, "MB1": 64.7}),
        raw_scores=MappingProxyType({"NEO": 10.564506231433699, "MB1": 64.3}),
    )


def _success_response(correlation_id: str = "ui-test") -> CalculateNeoRatingResponse:
    return CalculateNeoRatingResponse(
        status=ResponseStatus.SUCCESS,
        ratings=(_rating(),),
        problems=(),
        scientific_identity=_identity(),
        correlation_id=correlation_id,
    )


class ImmediateThreadPool:
    def start(self, worker) -> None:
        worker.run()


class SuccessfulUseCase:
    def execute(self, request):
        return _success_response(request.correlation_id)


class ValidationUseCase:
    def execute(self, request):
        return CalculateNeoRatingResponse(
            status=ResponseStatus.VALIDATION_ERROR,
            ratings=(),
            problems=(
                InputProblem(
                    code="LINE_TOO_SHORT",
                    severity=ProblemSeverity.ERROR,
                    message_key="error.line_too_short",
                    line_number=2,
                ),
            ),
            scientific_identity=None,
            correlation_id=request.correlation_id,
        )


class ThreadRecordingUseCase:
    def __init__(self) -> None:
        self.thread_id: int | None = None

    def execute(self, request):
        self.thread_id = threading.get_ident()
        return _success_response(request.correlation_id)


def test_initial_and_ready_states(qapp) -> None:
    window = MainWindow(SuccessfulUseCase(), thread_pool=ImmediateThreadPool())

    assert window.state is WindowState.EMPTY
    assert window.calculate_button.isEnabled() is False
    assert window.results_group.isVisible() is False

    window.observations_edit.setPlainText("observation")

    assert window.state is WindowState.READY
    assert window.calculate_button.isEnabled() is True
    window.close()


def test_success_populates_results_and_enables_copy(qapp) -> None:
    window = MainWindow(SuccessfulUseCase(), thread_pool=ImmediateThreadPool())
    window.observations_edit.setPlainText("observation")

    QTest.mouseClick(window.calculate_button, Qt.MouseButton.LeftButton)

    assert window.state is WindowState.SUCCESS
    assert window.results_table.rowCount() == 1
    assert window.results_table.item(0, 0).text() == "K16S99K"
    assert window.results_table.item(0, 2).text() == "20"
    assert window.copy_button.isEnabled() is True

    QTest.mouseClick(window.copy_button, Qt.MouseButton.LeftButton)
    assert "K16S99K" in qapp.clipboard().text()
    assert "20" in qapp.clipboard().text()
    window.close()


def test_validation_problem_is_shown_with_original_line(qapp) -> None:
    window = MainWindow(ValidationUseCase(), thread_pool=ImmediateThreadPool())
    window.observations_edit.setPlainText("invalid")

    QTest.mouseClick(window.calculate_button, Qt.MouseButton.LeftButton)

    assert window.state is WindowState.ERROR
    assert window.problems_list.count() == 1
    assert "line 2" in window.problems_list.item(0).text()
    assert "fewer than 80 characters" in window.problems_list.item(0).text()
    assert window.problems_list.item(0).toolTip() == "LINE_TOO_SHORT"
    assert window.results_table.rowCount() == 0
    window.close()


def test_editing_after_success_invalidates_previous_result(qapp) -> None:
    window = MainWindow(SuccessfulUseCase(), thread_pool=ImmediateThreadPool())
    window.observations_edit.setPlainText("observation")
    QTest.mouseClick(window.calculate_button, Qt.MouseButton.LeftButton)

    window.observations_edit.appendPlainText("changed")

    assert window.state is WindowState.READY
    assert window.results_table.rowCount() == 0
    assert window.copy_button.isEnabled() is False
    window.close()


def test_real_thread_pool_runs_use_case_outside_gui_thread(qapp) -> None:
    use_case = ThreadRecordingUseCase()
    window = MainWindow(use_case)
    window.observations_edit.setPlainText("observation")
    gui_thread_id = threading.get_ident()

    QTest.mouseClick(window.calculate_button, Qt.MouseButton.LeftButton)
    for _ in range(100):
        if window.state is WindowState.SUCCESS:
            break
        QTest.qWait(10)

    assert window.state is WindowState.SUCCESS
    assert use_case.thread_id is not None
    assert use_case.thread_id != gui_thread_id
    window.close()
    assert QThreadPool.globalInstance().waitForDone(5000) is True
