"""Main NEO Rating window."""

from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from PySide6.QtCore import Qt, QThreadPool, QTimer, Slot
from PySide6.QtGui import QCloseEvent, QFontDatabase, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from neo_rating.application.use_cases import CalculateNeoRating
from neo_rating.application.update_use_cases import CheckAndStageUpdate
from neo_rating import __version__
from neo_rating.domain.models import (
    CalculateNeoRatingRequest,
    CalculateNeoRatingResponse,
    ProblemSeverity,
    ResponseStatus,
    ScientificIdentity,
    TrackletRating,
)
from neo_rating.domain.updates import UpdateResult, UpdateStatus
from neo_rating.presentation.worker import CalculationWorker, UpdateWorker


class WindowState(StrEnum):
    EMPTY = "empty"
    READY = "ready"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


class MainWindow(QMainWindow):
    def __init__(
        self,
        use_case: CalculateNeoRating,
        *,
        thread_pool: QThreadPool | None = None,
        update_use_case: CheckAndStageUpdate | None = None,
    ) -> None:
        super().__init__()
        self._use_case = use_case
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._active_worker: CalculationWorker | None = None
        self._update_use_case = update_use_case
        self._update_worker: UpdateWorker | None = None
        self._ratings: tuple[TrackletRating, ...] = ()
        self._scientific_identity: ScientificIdentity | None = None
        self._state = WindowState.EMPTY

        self.setWindowTitle(self.tr("NEO Rating"))
        self.setMinimumSize(840, 620)
        self.resize(980, 720)
        self._build_ui()
        self._connect_signals()
        self._apply_styles()
        self._clear_output()
        self._set_state(WindowState.EMPTY)
        if self._update_use_case is not None:
            QTimer.singleShot(0, self._start_update_check)

    @property
    def state(self) -> WindowState:
        return self._state

    def _build_ui(self) -> None:
        central = QWidget(self)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        title = QLabel(self.tr("NEO Rating"))
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            self.tr("Official Digest2 classification for MPC 80-column observations")
        )
        subtitle.setObjectName("subtitle")
        outer.addWidget(title)
        outer.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider)

        input_header = QHBoxLayout()
        input_label = QLabel(self.tr("MPC Observations"))
        input_label.setObjectName("sectionTitle")
        self.input_summary_label = QLabel(self.tr("No lines"))
        self.input_summary_label.setObjectName("secondaryText")
        input_header.addWidget(input_label)
        input_header.addStretch()
        input_header.addWidget(self.input_summary_label)
        outer.addLayout(input_header)

        self.observations_edit = QPlainTextEdit()
        self.observations_edit.setAccessibleName(
            self.tr("MPC 80-column observations")
        )
        self.observations_edit.setPlaceholderText(
            self.tr("Paste two or more MPC 80-column observations here.")
        )
        self.observations_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.observations_edit.setFont(fixed_font)
        outer.addWidget(self.observations_edit, 3)

        actions = QHBoxLayout()
        self.calculate_button = QPushButton(self.tr("Calculate"))
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.setDefault(True)
        self.clear_button = QPushButton(self.tr("Clear"))
        self.copy_button = QPushButton(self.tr("Copy Results"))
        self.info_button = QPushButton(self.tr("Information"))
        actions.addWidget(self.calculate_button)
        actions.addWidget(self.clear_button)
        actions.addStretch()
        actions.addWidget(self.copy_button)
        actions.addWidget(self.info_button)
        outer.addLayout(actions)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        outer.addWidget(self.status_label)

        self.problems_group = QGroupBox(self.tr("Validation"))
        problems_layout = QVBoxLayout(self.problems_group)
        self.problems_list = QListWidget()
        self.problems_list.setAccessibleName(self.tr("Validation issues"))
        problems_layout.addWidget(self.problems_list)
        outer.addWidget(self.problems_group)

        self.results_group = QGroupBox(self.tr("Results"))
        results_layout = QVBoxLayout(self.results_group)
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(
            (
                self.tr("Designation"),
                self.tr("Observations"),
                self.tr("NEO Rating"),
                self.tr("RMS"),
                self.tr("Top Class"),
            )
        )
        self.results_table.setAccessibleName(self.tr("Digest2 results"))
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.results_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.results_table.verticalHeader().setVisible(False)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        results_layout.addWidget(self.results_table)
        outer.addWidget(self.results_group, 2)

        self.setCentralWidget(central)
        self.statusBar().showMessage(
            self.tr("Digest2 2.8.1 · local offline processing")
        )

    def _connect_signals(self) -> None:
        self.observations_edit.textChanged.connect(self._on_text_changed)
        self.calculate_button.clicked.connect(self._start_calculation)
        self.clear_button.clicked.connect(self._clear)
        self.copy_button.clicked.connect(self._copy_results)
        self.info_button.clicked.connect(self._show_information)

    @Slot()
    def _start_update_check(self) -> None:
        if self._update_use_case is None or self._update_worker is not None:
            return
        worker = UpdateWorker(self._update_use_case)
        worker.signals.completed.connect(self._update_check_completed)
        self._update_worker = worker
        self._thread_pool.start(worker)

    @Slot(object)
    def _update_check_completed(self, result: UpdateResult) -> None:
        self._update_worker = None
        if result.status is UpdateStatus.STAGED:
            self.statusBar().showMessage(
                self.tr(
                    "Update {version} was downloaded and verified."
                ).format(version=result.version),
                10000,
            )

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #121820;
                color: #e8edf3;
            }
            QMainWindow {
                border: none;
            }
            QLabel#pageTitle {
                color: #f7f9fc;
                font-size: 24px;
                font-weight: 600;
            }
            QLabel#subtitle, QLabel#secondaryText {
                color: #8f9cab;
            }
            QLabel#sectionTitle { font-size: 15px; font-weight: 600; }
            QFrame[frameShape="4"], QFrame[frameShape="5"] {
                color: #303b49;
            }
            QPlainTextEdit {
                background-color: #0b1016;
                color: #dbe7f3;
                border: 1px solid #344252;
                border-radius: 6px;
                padding: 10px;
                selection-background-color: #1479cc;
                selection-color: #ffffff;
            }
            QPushButton {
                min-height: 32px;
                padding: 0 16px;
                color: #e8edf3;
                background-color: #25313e;
                border: 1px solid #3a4959;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #303e4d; }
            QPushButton:pressed { background-color: #1d2732; }
            QPushButton:disabled {
                color: #687584;
                background-color: #1a232d;
                border-color: #293542;
            }
            QPushButton#primaryButton {
                font-weight: 600;
                background-color: #087dcc;
                color: #ffffff;
                border-color: #1494ed;
            }
            QPushButton#primaryButton:hover { background-color: #1290e5; }
            QGroupBox {
                font-weight: 600;
                margin-top: 10px;
                padding-top: 10px;
                border: 1px solid #303b49;
                border-radius: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #cbd5df;
            }
            QListWidget, QTableWidget {
                background-color: #0d131a;
                color: #e2e8ef;
                border: 1px solid #344252;
                gridline-color: #293542;
                alternate-background-color: #141d26;
                selection-background-color: #145f96;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #1d2834;
                color: #dce5ee;
                border: none;
                border-right: 1px solid #344252;
                border-bottom: 1px solid #344252;
                padding: 7px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #111820;
                border: none;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #3b4a5a;
                border-radius: 4px;
                min-height: 24px;
                min-width: 24px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0;
                height: 0;
            }
            QStatusBar {
                background-color: #0d131a;
                color: #94a2b1;
                border-top: 1px solid #293542;
            }
            QToolTip {
                color: #f4f7fa;
                background-color: #263443;
                border: 1px solid #526477;
            }
            """
        )

    @Slot()
    def _on_text_changed(self) -> None:
        if self._state is WindowState.PROCESSING:
            return
        text = self.observations_edit.toPlainText()
        line_count = len(text.splitlines()) if text else 0
        self.input_summary_label.setText(
            self.tr("{line_count} line(s)").format(line_count=line_count)
            if line_count
            else self.tr("No lines")
        )
        self._clear_output()
        self._set_state(WindowState.READY if text.strip() else WindowState.EMPTY)

    @Slot()
    def _start_calculation(self) -> None:
        if self._active_worker is not None:
            return

        request = CalculateNeoRatingRequest(
            source_text=self.observations_edit.toPlainText(),
            correlation_id=str(uuid4()),
        )
        worker = CalculationWorker(self._use_case, request)
        worker.signals.completed.connect(self._calculation_completed)
        worker.signals.failed.connect(self._worker_failed)
        self._active_worker = worker
        self._set_state(WindowState.PROCESSING)
        self._thread_pool.start(worker)

    @Slot(object)
    def _calculation_completed(self, response: CalculateNeoRatingResponse) -> None:
        self._active_worker = None
        self._show_problems(response)
        if response.status is ResponseStatus.SUCCESS:
            self._ratings = response.ratings
            self._scientific_identity = response.scientific_identity
            self._show_ratings(response.ratings)
            self._set_state(WindowState.SUCCESS)
            return
        self._ratings = ()
        self._set_state(WindowState.ERROR)

    @Slot(str)
    def _worker_failed(self, error_code: str) -> None:
        self._active_worker = None
        self.problems_list.clear()
        self.problems_list.addItem(
            self.tr("The calculation could not be completed. Code: {code}").format(
                code=error_code
            )
        )
        self.problems_group.setVisible(True)
        self._set_state(WindowState.ERROR)

    def _show_problems(self, response: CalculateNeoRatingResponse) -> None:
        self.problems_list.clear()
        for problem in response.problems:
            prefix = (
                self.tr("Error")
                if problem.severity is ProblemSeverity.ERROR
                else self.tr("Warning")
            )
            location = (
                self.tr("line {line_number}").format(
                    line_number=problem.line_number
                )
                if problem.line_number is not None
                else self.tr("input")
            )
            item = QListWidgetItem(
                self.tr("{prefix} · {location} · {message}").format(
                    prefix=prefix,
                    location=location,
                    message=self._problem_message(problem.message_key, problem.code),
                )
            )
            item.setData(Qt.ItemDataRole.UserRole, problem.message_key)
            item.setToolTip(problem.code)
            self.problems_list.addItem(item)
        self.problems_group.setVisible(bool(response.problems))

    def _show_ratings(self, ratings: tuple[TrackletRating, ...]) -> None:
        self.results_table.setRowCount(len(ratings))
        for row, rating in enumerate(ratings):
            values = (
                rating.designation,
                str(rating.observation_count),
                f"{rating.neo_rating:.0f}",
                f"{rating.rms_arcsec:.2f}″" if rating.rms_arcsec else "—",
                rating.top_noid_class,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (1, 2, 3):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if column == 2:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.results_table.setItem(row, column, item)
        self.results_group.setVisible(bool(ratings))

    def _set_state(self, state: WindowState) -> None:
        self._state = state
        processing = state is WindowState.PROCESSING
        has_input = bool(self.observations_edit.toPlainText().strip())
        self.observations_edit.setReadOnly(processing)
        self.calculate_button.setEnabled(has_input and not processing)
        self.clear_button.setEnabled(not processing and (has_input or bool(self._ratings)))
        self.copy_button.setEnabled(not processing and bool(self._ratings))

        messages = {
            WindowState.EMPTY: self.tr("Paste MPC observations to begin."),
            WindowState.READY: self.tr("Input changed. Click Calculate."),
            WindowState.PROCESSING: self.tr("Calculating with official Digest2…"),
            WindowState.SUCCESS: self.tr("Calculation completed."),
            WindowState.ERROR: self.tr("Review the validation issues."),
        }
        self.status_label.setText(messages[state])

    def _clear_output(self) -> None:
        self._ratings = ()
        self._scientific_identity = None
        self.results_table.setRowCount(0)
        self.results_group.setVisible(False)
        self.problems_list.clear()
        self.problems_group.setVisible(False)

    @Slot()
    def _clear(self) -> None:
        self.observations_edit.clear()
        self._clear_output()
        self._set_state(WindowState.EMPTY)
        self.observations_edit.setFocus()

    @Slot()
    def _copy_results(self) -> None:
        if not self._ratings:
            return
        lines = [self.tr("Designation\tObservations\tNEO Rating\tRMS\tTop Class")]
        for rating in self._ratings:
            rms = f"{rating.rms_arcsec:.2f}″" if rating.rms_arcsec else "—"
            lines.append(
                "{designation}\t{count}\t{rating:.0f}\t{rms}\t{top_class}".format(
                    designation=rating.designation,
                    count=rating.observation_count,
                    rating=rating.neo_rating,
                    rms=rms,
                    top_class=rating.top_noid_class,
                )
            )
        QGuiApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage(self.tr("Results copied."), 3000)

    def _problem_message(self, message_key: str, code: str) -> str:
        messages = {
            "error.input_empty": self.tr("Paste observations before calculating."),
            "warning.line_empty": self.tr("The line is empty and was ignored."),
            "warning.line_trailing_padding": self.tr(
                "Extra spaces or tabs after column 80 were ignored; observation columns were preserved."
            ),
            "error.line_too_short": self.tr("The line has fewer than 80 characters."),
            "error.line_too_long": self.tr(
                "The line has more than 80 characters. Check extra text or shifted fields; the observatory code must be in columns 78–80."
            ),
            "error.line_non_ascii": self.tr("The line contains non-ASCII characters."),
            "error.line_unsupported": self.tr(
                "The observation type is not supported."
            ),
            "error.line_parse_failed": self.tr(
                "The official parser did not recognize the observation."
            ),
            "error.line_field_designation": self.tr("The designation is missing."),
            "error.line_field_date": self.tr("The observation date is invalid."),
            "error.line_field_ra": self.tr("The right ascension is invalid."),
            "error.line_field_dec": self.tr("The declination is invalid."),
            "error.line_field_magnitude": self.tr("The magnitude is invalid."),
            "error.line_field_obscode": self.tr(
                "The observatory code is missing."
            ),
            "error.orphan_auxiliary_line": self.tr(
                "The auxiliary line has no corresponding primary observation."
            ),
            "error.auxiliary_parse_failed": self.tr(
                "The official parser rejected the auxiliary line."
            ),
            "error.tracklet_too_short": self.tr(
                "The tracklet requires at least two observations."
            ),
            "error.tracklet_time_order": self.tr(
                "The tracklet observations are not in chronological order."
            ),
            "error.scientific_file_missing": self.tr(
                "A required scientific file is missing."
            ),
            "error.scientific_file_hash": self.tr(
                "A scientific file does not match the approved version."
            ),
            "error.digest2_init_failed": self.tr(
                "The official Digest2 engine could not be initialized."
            ),
            "error.digest2_classify_failed": self.tr(
                "Digest2 could not classify the observations."
            ),
            "error.unexpected_failure": self.tr(
                "An unexpected failure occurred during calculation."
            ),
        }
        return messages.get(
            message_key,
            self.tr("Unrecognized issue. Code: {code}").format(code=code),
        )

    @Slot()
    def _show_information(self) -> None:
        identity = self._scientific_identity
        if identity is None:
            text = self.tr(
                "NEO Rating {app_version}\n"
                "Digest2 2.8.1\n\n"
                "Scientific files are verified before every calculation.\n"
                "The application runs locally and performs no automatic downloads."
            ).format(app_version=__version__)
        else:
            text = self.tr(
                "NEO Rating {app_version}\n"
                "Digest2 {digest2_version}\n"
                "Repeatable mode: {repeatable}\n\n"
                "CSV model: {model_hash}\n"
                "Runtime model: {runtime_hash}\n"
                "MPC configuration: {config_hash}\n"
                "Observatory codes: {obscodes_hash}"
            ).format(
                app_version=identity.application_version,
                digest2_version=identity.digest2_version,
                repeatable=self.tr("yes") if identity.repeatable else self.tr("no"),
                model_hash=identity.model_sha256,
                runtime_hash=identity.runtime_model_sha256,
                config_hash=identity.config_sha256,
                obscodes_hash=identity.obscodes_sha256,
            )
        QMessageBox.information(
            self,
            self.tr("Scientific Information"),
            text,
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._active_worker is None:
            event.accept()
            return
        answer = QMessageBox.question(
            self,
            self.tr("Calculation in Progress"),
            self.tr("A calculation is in progress. Do you want to close the window?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer is QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
