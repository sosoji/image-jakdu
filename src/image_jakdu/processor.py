from __future__ import annotations

from pathlib import PureWindowsPath
from typing import TYPE_CHECKING

from image_jakdu.pipeline import run_batch_workflow

if TYPE_CHECKING:
    from collections.abc import Callable

    from image_jakdu.gui.job import GuiProcessRequest


def save_batch_workflow(
    request: GuiProcessRequest,
    report_progress: Callable[[int, int, str], None],
    is_cancel_requested: Callable[[], bool],
) -> tuple[PureWindowsPath, ...]:
    result = run_batch_workflow(request, report_progress, is_cancel_requested)
    return tuple(PureWindowsPath(str(item)) for item in result.saved)
