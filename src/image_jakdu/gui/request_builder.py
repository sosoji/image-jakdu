from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from image_jakdu.domain import (
    AutoDetectSettings,
    CountGridSettings,
    ModeName,
    PixelSizeSettings,
    ValidationFailure,
)
from image_jakdu.gui.job import GuiProcessRequest

if TYPE_CHECKING:
    from pathlib import PureWindowsPath

ModeLabelByText: Final[dict[str, ModeName]] = {
    "Count grid": "count_grid",
    "Pixel size": "pixel_size",
    "Auto detect": "auto_detect",
    "Model assisted": "model_assisted",
}


@dataclass(frozen=True, slots=True)
class JobRequestFields:
    selected_sources: tuple[PureWindowsPath, ...]
    selected_output_folder: PureWindowsPath | None
    selected_mode_text: str
    columns: int
    rows: int
    tile_width: int
    tile_height: int
    use_model_assist: bool
    auto_trim_margins: bool


def build_job_request(fields: JobRequestFields) -> GuiProcessRequest:
    if fields.selected_output_folder is None:
        message = "output folder is required before processing"
        raise ValidationFailure(message)
    mode = ModeLabelByText[fields.selected_mode_text]
    match mode:
        case "count_grid":
            settings: CountGridSettings | PixelSizeSettings | AutoDetectSettings = (
                CountGridSettings(columns=fields.columns, rows=fields.rows)
            )
        case "pixel_size":
            settings = PixelSizeSettings(
                tile_width=fields.tile_width,
                tile_height=fields.tile_height,
            )
        case _:
            settings = AutoDetectSettings()
    return GuiProcessRequest(
        sources=fields.selected_sources,
        output_folder=fields.selected_output_folder,
        mode=mode,
        settings=settings,
        use_model_assist=fields.use_model_assist,
        auto_trim_margins=fields.auto_trim_margins,
    )
