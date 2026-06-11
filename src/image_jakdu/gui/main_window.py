from __future__ import annotations

from collections.abc import Callable
from pathlib import PureWindowsPath

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)

from image_jakdu.domain import (
    CountGridSettings,
    IntentJobDraft,
    PixelSizeSettings,
    ValidationFailure,
)
from image_jakdu.gui.job_controller import GuiJobController
from image_jakdu.gui.layout import WindowLayoutParts, build_window_layout
from image_jakdu.gui.request_builder import JobRequestFields, build_job_request
from image_jakdu.gui.support import (
    MODE_LABEL,
    default_output_picker,
    default_source_picker,
    make_group_box,
    make_spin_box,
    manual_intent_provider,
    summarize_draft,
)
from image_jakdu.gui.worker import (
    ProcessFn,
    ProcessWorker,
    default_processor,
)

SourcePicker = Callable[[QWidget], tuple[str, ...]]
OutputPicker = Callable[[QWidget], str]
IntentProvider = Callable[[str], str]


class ImageJakduWindow(QMainWindow):
    def __init__(
        self,
        *,
        intent_provider: IntentProvider | None = None,
        source_picker: SourcePicker | None = None,
        output_picker: OutputPicker | None = None,
        process: ProcessFn | None = None,
    ) -> None:
        super().__init__()
        self._intent_provider: IntentProvider = intent_provider or manual_intent_provider
        self._source_picker: SourcePicker = source_picker or default_source_picker
        self._output_picker: OutputPicker = output_picker or default_output_picker
        self._processor: ProcessFn = process or default_processor
        self.selected_sources: tuple[PureWindowsPath, ...] = ()
        self.selected_output_folder: PureWindowsPath | None = None
        self._next_job_id: int = 1
        self.brand_label: QLabel = QLabel("이미지 작두 / Image Jakdu")
        self.source_label: QLabel = QLabel("No images selected")
        self.output_label: QLabel = QLabel("No output folder selected")
        self.select_sources_button: QPushButton = QPushButton("Select images")
        self.select_output_button: QPushButton = QPushButton("Select output folder")
        self.mode_selector: QComboBox = QComboBox()
        self.mode_selector.addItems(tuple(MODE_LABEL.values()))
        self.columns_input: QSpinBox = make_spin_box(default=2)
        self.rows_input: QSpinBox = make_spin_box(default=2)
        self.tile_width_input: QSpinBox = make_spin_box(default=32)
        self.tile_height_input: QSpinBox = make_spin_box(default=32)
        self.model_assist_checkbox: QCheckBox = QCheckBox("Model assist")
        self.auto_trim_checkbox: QCheckBox = QCheckBox("Auto trim margins")
        self.intent_text: QTextEdit = QTextEdit()
        self.intent_button: QPushButton = QPushButton("Clarify intent")
        self.validation_label: QLabel = QLabel("")
        self.preview_label: QLabel = QLabel("No split preview yet.")
        self.process_button: QPushButton = QPushButton("Process")
        self.cancel_button: QPushButton = QPushButton("Cancel")
        self.progress_bar: QProgressBar = QProgressBar()
        self.status_label: QLabel = QLabel("Select images and an output folder.")
        self._jobs: GuiJobController = GuiJobController(
            status_label=self.status_label,
            validation_label=self.validation_label,
            progress_bar=self.progress_bar,
            process_button=self.process_button,
            cancel_button=self.cancel_button,
        )
        self.count_controls: QGroupBox = make_group_box(
            "Count grid",
            (QLabel("Columns"), self.columns_input, QLabel("Rows"), self.rows_input),
        )
        self.pixel_controls: QGroupBox = make_group_box(
            "Pixel size",
            (
                QLabel("Tile width"),
                self.tile_width_input,
                QLabel("Tile height"),
                self.tile_height_input,
            ),
        )
        build_window_layout(
            self,
            WindowLayoutParts(
                brand_label=self.brand_label,
                select_sources_button=self.select_sources_button,
                select_output_button=self.select_output_button,
                source_label=self.source_label,
                output_label=self.output_label,
                mode_selector=self.mode_selector,
                count_controls=self.count_controls,
                pixel_controls=self.pixel_controls,
                model_assist_checkbox=self.model_assist_checkbox,
                auto_trim_checkbox=self.auto_trim_checkbox,
                intent_text=self.intent_text,
                intent_button=self.intent_button,
                validation_label=self.validation_label,
                preview_label=self.preview_label,
                progress_bar=self.progress_bar,
                status_label=self.status_label,
                process_button=self.process_button,
                cancel_button=self.cancel_button,
            ),
        )
        _ = self.select_sources_button.clicked.connect(self.choose_source_files)
        _ = self.select_output_button.clicked.connect(self.choose_output_folder)
        _ = self.intent_button.clicked.connect(self.clarify_intent)
        _ = self.process_button.clicked.connect(self.start_processing)
        _ = self.cancel_button.clicked.connect(self.cancel_processing)
        _ = self.mode_selector.currentTextChanged.connect(self._sync_mode_controls)
        self._sync_mode_controls()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(False)
        self._sync_process_enabled()

    def choose_source_files(self) -> None:
        files = self._source_picker(self)
        if len(files) == 0:
            return
        self.set_source_files(tuple(PureWindowsPath(file_name) for file_name in files))

    def choose_output_folder(self) -> None:
        folder = self._output_picker(self)
        if folder == "":
            return
        self.set_output_folder(PureWindowsPath(folder))

    def clarify_intent(self) -> None:
        try:
            raw_json = self._intent_provider(self.intent_text.toPlainText())
            self.apply_intent_json(raw_json)
        except ValidationFailure as exc:
            self.validation_label.setText(str(exc))
            self.status_label.setText("Intent could not be applied.")
            return
        self.validation_label.setText("")
        self.status_label.setText("Intent applied.")

    def set_source_files(self, paths: tuple[PureWindowsPath, ...]) -> None:
        self.selected_sources = paths
        self.source_label.setText("; ".join(str(path) for path in paths))
        if self._jobs.worker is None:
            self.status_label.setText(f"Ready to process {len(paths)} image(s).")
        self._sync_process_enabled()

    def set_output_folder(self, path: PureWindowsPath) -> None:
        self.selected_output_folder = path
        self.output_label.setText(str(path))
        if self._jobs.worker is None and len(self.selected_sources) > 0:
            self.status_label.setText(f"Ready to process {len(self.selected_sources)} image(s).")
        self._sync_process_enabled()

    def apply_intent_json(self, raw_json: str) -> None:
        draft = IntentJobDraft.from_json(raw_json)
        self.model_assist_checkbox.setChecked(draft.use_model_assist)
        self.auto_trim_checkbox.setChecked(draft.auto_trim_margins)
        self.preview_label.setText(summarize_draft(draft, MODE_LABEL))
        settings = draft.settings
        match settings:
            case CountGridSettings(columns=columns, rows=rows):
                self.mode_selector.setCurrentText(MODE_LABEL["count_grid"])
                self.columns_input.setValue(columns)
                self.rows_input.setValue(rows)
            case PixelSizeSettings(tile_width=tile_width, tile_height=tile_height):
                self.mode_selector.setCurrentText(MODE_LABEL["pixel_size"])
                self.tile_width_input.setValue(tile_width)
                self.tile_height_input.setValue(tile_height)
            case _:
                self.mode_selector.setCurrentText(MODE_LABEL[draft.mode])

    def start_processing(self) -> None:
        if self._jobs.worker is not None:
            return
        if len(self.selected_sources) == 0 or self.selected_output_folder is None:
            self.validation_label.setText("Select at least one image and an output folder.")
            self.status_label.setText("Select images and an output folder before processing.")
            self._sync_process_enabled()
            return

        job_id = self._next_job_id
        self._next_job_id += 1
        self._jobs.active_job_id = job_id
        worker = ProcessWorker(
            job_id=job_id,
            request=build_job_request(
                JobRequestFields(
                    selected_sources=self.selected_sources,
                    selected_output_folder=self.selected_output_folder,
                    selected_mode_text=self.mode_selector.currentText(),
                    columns=self.columns_input.value(),
                    rows=self.rows_input.value(),
                    tile_width=self.tile_width_input.value(),
                    tile_height=self.tile_height_input.value(),
                    use_model_assist=self.model_assist_checkbox.isChecked(),
                    auto_trim_margins=self.auto_trim_checkbox.isChecked(),
                ),
            ),
            process=self._processor,
        )
        self._jobs.worker = worker
        _ = worker.progress.connect(self.on_progress)
        _ = worker.completed.connect(self.on_completed)
        _ = worker.cancelled.connect(self.on_cancelled)
        _ = worker.failed.connect(self.on_failed)
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing...")
        self.process_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        worker.start()

    def cancel_processing(self) -> None:
        if self._jobs.worker is None:
            return
        self._jobs.worker.request_cancel()
        self.status_label.setText("Cancel requested.")
        self.cancel_button.setEnabled(False)

    def _sync_mode_controls(self) -> None:
        selected = self.mode_selector.currentText()
        self.count_controls.setVisible(selected == MODE_LABEL["count_grid"])
        self.pixel_controls.setVisible(selected == MODE_LABEL["pixel_size"])

    def _sync_process_enabled(self) -> None:
        ready = (
            len(self.selected_sources) > 0
            and self.selected_output_folder is not None
            and self._jobs.worker is None
        )
        self.process_button.setEnabled(ready)

    def on_progress(self, job_id: int, processed: int, total: int, message: str) -> None:
        _ = self._jobs.on_progress(job_id, processed, total, message)

    def on_completed(self, job_id: int, outputs: tuple[PureWindowsPath, ...]) -> None:
        if self._jobs.on_completed(job_id, outputs):
            self._sync_process_enabled()

    def on_cancelled(self, job_id: int) -> None:
        if self._jobs.on_cancelled(job_id):
            self._sync_process_enabled()

    def on_failed(self, job_id: int, message: str) -> None:
        if self._jobs.on_failed(job_id, message):
            self._sync_process_enabled()
