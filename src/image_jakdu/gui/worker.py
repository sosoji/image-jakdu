from __future__ import annotations

from collections.abc import Callable
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, ClassVar

from PySide6.QtCore import QThread, Signal
from typing_extensions import override

from image_jakdu.processor import save_batch_workflow

if TYPE_CHECKING:
    from image_jakdu.gui.job import GuiProcessRequest

ProgressReporter = Callable[[int, int, str], None]
CancelProbe = Callable[[], bool]
ProcessFn = Callable[
    ["GuiProcessRequest", ProgressReporter, CancelProbe],
    tuple[PureWindowsPath, ...],
]


class ProcessWorker(QThread):
    progress: ClassVar[Signal] = Signal(int, int, int, str)
    completed: ClassVar[Signal] = Signal(int, tuple)
    failed: ClassVar[Signal] = Signal(int, str)
    cancelled: ClassVar[Signal] = Signal(int)

    def __init__(
        self,
        *,
        job_id: int,
        request: GuiProcessRequest,
        process: ProcessFn,
    ) -> None:
        super().__init__()
        self._job_id: int = job_id
        self._request: GuiProcessRequest = request
        self._process: ProcessFn = process
        self._cancel_requested: bool = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def is_cancel_requested(self) -> bool:
        return self._cancel_requested

    def _report_progress(self, processed: int, total: int, message: str) -> None:
        self.progress.emit(self._job_id, processed, total, message)

    @override
    def run(self) -> None:
        try:
            output_paths = self._process(
                self._request,
                self._report_progress,
                self.is_cancel_requested,
            )
            if self._cancel_requested:
                self.cancelled.emit(self._job_id)
                return
            self.completed.emit(self._job_id, output_paths)
        except Exception as exc:  # noqa: BLE001
            if self._cancel_requested:
                self.cancelled.emit(self._job_id)
            else:
                self.failed.emit(self._job_id, str(exc))


def default_processor(
    request: GuiProcessRequest,
    report_progress: ProgressReporter,
    is_cancel_requested: CancelProbe,
) -> tuple[PureWindowsPath, ...]:
    return save_batch_workflow(request, report_progress, is_cancel_requested)
