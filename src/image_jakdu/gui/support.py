from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QGroupBox, QHBoxLayout, QSpinBox, QWidget

from image_jakdu.domain import CountGridSettings, IntentJobDraft, ModeName, PixelSizeSettings

MODE_LABEL: dict[ModeName, str] = {
    "count_grid": "Count grid",
    "pixel_size": "Pixel size",
    "auto_detect": "Auto detect",
    "model_assisted": "Model assisted",
}


def make_spin_box(*, default: int) -> QSpinBox:
    spin_box = QSpinBox()
    spin_box.setMinimum(1)
    spin_box.setMaximum(100_000)
    spin_box.setValue(default)
    return spin_box


def make_group_box(title: str, widgets: tuple[QWidget, ...]) -> QGroupBox:
    group = QGroupBox(title)
    layout = QHBoxLayout(group)
    for widget in widgets:
        layout.addWidget(widget)
    return group


def manual_intent_provider(text: str) -> str:
    return text


def default_source_picker(parent: QWidget) -> tuple[str, ...]:
    files, _selected_filter = QFileDialog.getOpenFileNames(
        parent,
        "Select source images",
        "",
        "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All files (*)",
    )
    return tuple(files)


def default_output_picker(parent: QWidget) -> str:
    return QFileDialog.getExistingDirectory(parent, "Select output folder")


def summarize_draft(draft: IntentJobDraft, mode_label: dict[ModeName, str]) -> str:
    settings = draft.settings
    match settings:
        case CountGridSettings(columns=columns, rows=rows):
            return f"Count grid: {columns} columns x {rows} rows"
        case PixelSizeSettings(tile_width=tile_width, tile_height=tile_height):
            return f"Pixel size: {tile_width}px x {tile_height}px"
        case _:
            return f"{mode_label[draft.mode]}: auto boundary detection"
