from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import PureWindowsPath

    from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QTextEdit


class ClearableWindow(Protocol):
    selected_sources: tuple[PureWindowsPath, ...]
    selected_output_folder: PureWindowsPath | None
    source_label: QLabel
    output_label: QLabel
    intent_text: QTextEdit
    validation_label: QLabel
    preview_label: QLabel
    progress_bar: QProgressBar
    status_label: QLabel
    process_button: QPushButton
    cancel_button: QPushButton


def reset_clearable_state(window: ClearableWindow, *, worker_is_active: bool) -> None:
    if worker_is_active:
        return
    window.selected_sources = ()
    window.selected_output_folder = None
    window.source_label.setText("No images selected")
    window.output_label.setText("No output folder selected")
    window.intent_text.clear()
    window.validation_label.setText("")
    window.preview_label.setText("No split preview yet.")
    window.progress_bar.setValue(0)
    window.status_label.setText("Select images and an output folder.")
    window.cancel_button.setEnabled(False)
    window.process_button.setEnabled(False)
