from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PureWindowsPath

    from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton

    from image_jakdu.gui.worker import ProcessWorker


class GuiJobController:
    def __init__(
        self,
        *,
        status_label: QLabel,
        validation_label: QLabel,
        progress_bar: QProgressBar,
        process_button: QPushButton,
        cancel_button: QPushButton,
    ) -> None:
        self.active_job_id: int | None = None
        self.worker: ProcessWorker | None = None
        self.status_label: QLabel = status_label
        self.validation_label: QLabel = validation_label
        self.progress_bar: QProgressBar = progress_bar
        self.process_button: QPushButton = process_button
        self.cancel_button: QPushButton = cancel_button

    def on_progress(self, job_id: int, processed: int, total: int, message: str) -> bool:
        if self.active_job_id != job_id:
            return False
        bounded_total = max(total, 1)
        percent = int((processed / bounded_total) * 100)
        self.progress_bar.setValue(max(0, min(100, percent)))
        if message:
            self.status_label.setText(f"{message} ({processed}/{bounded_total})")
        else:
            self.status_label.setText(f"Progress: {percent}%")
        return True

    def on_completed(self, job_id: int, outputs: tuple[PureWindowsPath, ...]) -> bool:
        if self.active_job_id != job_id:
            return False
        self.worker = None
        self.active_job_id = None
        self.status_label.setText(f"Process complete: {len(outputs)} output(s) saved.")
        self.progress_bar.setValue(100)
        self.cancel_button.setEnabled(False)
        return True

    def on_cancelled(self, job_id: int) -> bool:
        if self.active_job_id != job_id:
            return False
        self.worker = None
        self.active_job_id = None
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing cancelled.")
        self.cancel_button.setEnabled(False)
        return True

    def on_failed(self, job_id: int, message: str) -> bool:
        if self.active_job_id != job_id:
            return False
        self.worker = None
        self.active_job_id = None
        self.progress_bar.setValue(0)
        self.validation_label.setText(message)
        self.status_label.setText("Processing failed.")
        self.cancel_button.setEnabled(False)
        return True
