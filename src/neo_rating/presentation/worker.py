"""Background execution of application use cases."""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from neo_rating.application.use_cases import CalculateNeoRating
from neo_rating.domain.models import CalculateNeoRatingRequest


class CalculationSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)


class CalculationWorker(QRunnable):
    def __init__(
        self,
        use_case: CalculateNeoRating,
        request: CalculateNeoRatingRequest,
    ) -> None:
        super().__init__()
        self.signals = CalculationSignals()
        self._use_case = use_case
        self._request = request

    @Slot()
    def run(self) -> None:
        try:
            response = self._use_case.execute(self._request)
        except Exception:
            self.signals.failed.emit("UNEXPECTED_WORKER_FAILURE")
            return
        self.signals.completed.emit(response)

