from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PureWindowsPath

    from image_jakdu.domain import (
        AutoDetectSettings,
        CountGridSettings,
        ModeName,
        PixelSizeSettings,
    )


@dataclass(frozen=True, slots=True)
class GuiProcessRequest:
    sources: tuple[PureWindowsPath, ...]
    output_folder: PureWindowsPath
    mode: ModeName
    settings: CountGridSettings | PixelSizeSettings | AutoDetectSettings
    use_model_assist: bool
    auto_trim_margins: bool
    write_metadata: bool = False
