from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PySide6.QtCore import QThread, Signal
from typing_extensions import override

if TYPE_CHECKING:
    from image_jakdu.codex_help import CodexHelpProvider


class CodexHelpWorker(QThread):
    completed: ClassVar[Signal] = Signal(str)
    failed: ClassVar[Signal] = Signal(str)

    def __init__(self, *, instruction: str, provider: CodexHelpProvider) -> None:
        super().__init__()
        self._instruction: str = instruction
        self._provider: CodexHelpProvider = provider

    @override
    def run(self) -> None:
        try:
            answer = self._provider(self._instruction)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.completed.emit(answer)
