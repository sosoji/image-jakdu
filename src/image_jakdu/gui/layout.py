from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget


@dataclass(frozen=True, slots=True)
class WindowLayoutParts:
    brand_label: QLabel
    select_sources_button: QWidget
    select_output_button: QWidget
    source_label: QLabel
    output_label: QLabel
    mode_selector: QWidget
    count_controls: QWidget
    pixel_controls: QWidget
    model_assist_checkbox: QWidget
    auto_trim_checkbox: QWidget
    intent_text: QWidget
    intent_button: QWidget
    validation_label: QLabel
    preview_label: QLabel
    progress_bar: QWidget
    status_label: QLabel
    process_button: QWidget
    cancel_button: QWidget


def build_window_layout(window: QMainWindow, parts: WindowLayoutParts) -> None:
    root = QWidget()
    layout = QVBoxLayout(root)
    layout.addWidget(parts.brand_label)
    picker_layout = QHBoxLayout()
    picker_layout.addWidget(parts.select_sources_button)
    picker_layout.addWidget(parts.select_output_button)
    layout.addLayout(picker_layout)
    layout.addWidget(parts.source_label)
    layout.addWidget(parts.output_label)
    layout.addWidget(parts.mode_selector)
    layout.addWidget(parts.count_controls)
    layout.addWidget(parts.pixel_controls)
    layout.addWidget(parts.model_assist_checkbox)
    layout.addWidget(parts.auto_trim_checkbox)
    layout.addWidget(parts.intent_text)
    layout.addWidget(parts.intent_button)
    layout.addWidget(parts.validation_label)
    layout.addWidget(parts.preview_label)
    layout.addWidget(parts.progress_bar)
    layout.addWidget(parts.status_label)
    buttons = QHBoxLayout()
    buttons.addWidget(parts.process_button)
    buttons.addWidget(parts.cancel_button)
    layout.addLayout(buttons)
    window.setCentralWidget(root)
