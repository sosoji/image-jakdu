from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from image_jakdu.domain import (
    CountGridSettings,
    IntentJobDraft,
    PixelSizeSettings,
    ValidationFailure,
)
from image_jakdu.gui.codex_help_worker import CodexHelpWorker
from image_jakdu.gui.support import MODE_LABEL, summarize_draft

if TYPE_CHECKING:
    from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QPushButton, QSpinBox, QTextEdit

    from image_jakdu.codex_help import CodexHelpProvider
    from image_jakdu.gui.selection import IntentProvider


class IntentActionWindow(Protocol):
    intent_text: QTextEdit
    validation_label: QLabel
    status_label: QLabel
    preview_label: QLabel
    model_assist_checkbox: QCheckBox
    auto_trim_checkbox: QCheckBox
    mode_selector: QComboBox
    columns_input: QSpinBox
    rows_input: QSpinBox
    tile_width_input: QSpinBox
    tile_height_input: QSpinBox


class CodexHelpActionWindow(IntentActionWindow, Protocol):
    codex_help_worker: CodexHelpWorker | None
    ask_codex_button: QPushButton

    def on_codex_help_completed(self, answer: str) -> None: ...

    def on_codex_help_failed(self, message: str) -> None: ...


def clarify_intent_for_window(
    window: IntentActionWindow,
    *,
    intent_provider: IntentProvider,
) -> None:
    try:
        raw_json = intent_provider(window.intent_text.toPlainText())
        apply_intent_json_to_window(window, raw_json)
    except ValidationFailure as exc:
        window.validation_label.setText(str(exc))
        window.status_label.setText("Intent could not be applied.")
        return
    window.validation_label.setText("")
    window.status_label.setText("Intent applied.")


def ask_codex_for_window(
    window: CodexHelpActionWindow,
    *,
    codex_help_provider: CodexHelpProvider,
) -> None:
    if window.codex_help_worker is not None:
        return
    instruction = window.intent_text.toPlainText().strip()
    if instruction == "":
        window.validation_label.setText("Enter a question before asking Codex.")
        window.status_label.setText("Codex help needs a question.")
        return
    worker = CodexHelpWorker(instruction=instruction, provider=codex_help_provider)
    window.codex_help_worker = worker
    _ = worker.completed.connect(window.on_codex_help_completed)
    _ = worker.failed.connect(window.on_codex_help_failed)
    window.validation_label.setText("")
    window.status_label.setText("Asking Codex...")
    window.ask_codex_button.setEnabled(False)
    worker.start()


def apply_codex_answer_to_window(window: CodexHelpActionWindow, answer: str) -> None:
    window.codex_help_worker = None
    window.ask_codex_button.setEnabled(True)
    window.validation_label.setText("")
    window.preview_label.setText(f"Codex: {answer}")
    window.status_label.setText("Codex help applied.")


def apply_codex_error_to_window(window: CodexHelpActionWindow, message: str) -> None:
    window.codex_help_worker = None
    window.ask_codex_button.setEnabled(True)
    window.validation_label.setText(message)
    window.status_label.setText("Codex help unavailable.")


def apply_intent_json_to_window(window: IntentActionWindow, raw_json: str) -> None:
    draft = IntentJobDraft.from_json(raw_json)
    window.model_assist_checkbox.setChecked(draft.use_model_assist)
    window.auto_trim_checkbox.setChecked(draft.auto_trim_margins)
    window.preview_label.setText(summarize_draft(draft, MODE_LABEL))
    settings = draft.settings
    match settings:
        case CountGridSettings(columns=columns, rows=rows):
            window.mode_selector.setCurrentText(MODE_LABEL["count_grid"])
            window.columns_input.setValue(columns)
            window.rows_input.setValue(rows)
        case PixelSizeSettings(tile_width=tile_width, tile_height=tile_height):
            window.mode_selector.setCurrentText(MODE_LABEL["pixel_size"])
            window.tile_width_input.setValue(tile_width)
            window.tile_height_input.setValue(tile_height)
        case _:
            window.mode_selector.setCurrentText(MODE_LABEL[draft.mode])
