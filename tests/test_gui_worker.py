from __future__ import annotations

import time
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING, final

from PIL import Image
from PySide6.QtWidgets import QApplication

from image_jakdu.gui.main_window import ImageJakduWindow

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytestqt.qtbot import QtBot

    from image_jakdu.gui.job import GuiProcessRequest
    from image_jakdu.gui.worker import ProgressReporter


@final
class ProgressCaptureProcessor:
    def __init__(
        self,
        output_dir: Path,
        *,
        write_results: bool = True,
        delay_seconds: float = 0.01,
    ) -> None:
        self.output_dir: Path = output_dir
        self.write_results: bool = write_results
        self.delay_seconds: float = delay_seconds
        self.progress_events: list[tuple[int, int, str]] = []

    def __call__(
        self,
        _request: GuiProcessRequest,
        report_progress: ProgressReporter,
        is_cancel_requested: Callable[[], bool],
    ) -> tuple[PureWindowsPath, ...]:
        for index in range(1, 4):
            if is_cancel_requested():
                return ()
            time.sleep(self.delay_seconds)
            report_progress(index, 3, f"chunk {index}")
            self.progress_events.append((index, 3, f"chunk {index}"))

        if self.write_results and not is_cancel_requested():
            first_output = self.output_dir / "result_1.png"
            _ = first_output.write_text("ok")
            return (PureWindowsPath(str(first_output)),)

        return ()


def test_worker_progress_and_completion_updates_status(qtbot: QtBot, tmp_path: Path) -> None:
    _ = QApplication.instance() or QApplication([])

    processor = ProgressCaptureProcessor(output_dir=tmp_path)
    window = ImageJakduWindow(process=processor)
    qtbot.addWidget(window)
    window.show()

    window.set_source_files((PureWindowsPath(r"C:\images\first.png"),))
    window.set_output_folder(PureWindowsPath(str(tmp_path)))

    window.process_button.click()
    qtbot.waitUntil(lambda: window.status_label.text().startswith("Process complete"), timeout=2000)

    assert window.status_label.text() == "Process complete: 1 output(s) saved."
    assert window.progress_bar.value() == 100
    assert len(processor.progress_events) == 3


def test_clear_after_completion_resets_ready_state(qtbot: QtBot, tmp_path: Path) -> None:
    _ = QApplication.instance() or QApplication([])

    processor = ProgressCaptureProcessor(output_dir=tmp_path)
    window = ImageJakduWindow(process=processor)
    qtbot.addWidget(window)
    window.show()

    window.set_source_files((PureWindowsPath(r"C:\images\first.png"),))
    window.set_output_folder(PureWindowsPath(str(tmp_path)))

    window.process_button.click()
    qtbot.waitUntil(lambda: window.status_label.text().startswith("Process complete"), timeout=2000)

    window.clear_button.click()

    assert window.selected_sources == ()
    assert window.selected_output_folder is None
    assert window.source_label.text() == "No images selected"
    assert window.output_label.text() == "No output folder selected"
    assert window.preview_label.text() == "No split preview yet."
    assert window.progress_bar.value() == 0
    assert window.status_label.text() == "Select images and an output folder."
    assert not window.process_button.isEnabled()
    assert not window.cancel_button.isEnabled()


def test_default_gui_processor_saves_split_images(qtbot: QtBot, tmp_path: Path) -> None:
    _ = QApplication.instance() or QApplication([])

    source = tmp_path / "source.png"
    Image.new("RGB", (8, 8), "white").save(source)
    output_dir = tmp_path / "out"

    window = ImageJakduWindow()
    qtbot.addWidget(window)
    window.show()
    window.set_source_files((PureWindowsPath(source),))
    window.set_output_folder(PureWindowsPath(output_dir))

    window.process_button.click()
    qtbot.waitUntil(lambda: window.status_label.text().startswith("Process complete"), timeout=2000)

    assert window.status_label.text() == "Process complete: 4 output(s) saved."
    assert sorted(path.name for path in output_dir.glob("*.png")) == [
        "source1.png",
        "source2.png",
        "source3.png",
        "source4.png",
    ]


def test_cancel_prevents_stale_result_save(qtbot: QtBot, tmp_path: Path) -> None:
    _ = QApplication.instance() or QApplication([])

    processor = ProgressCaptureProcessor(output_dir=tmp_path, delay_seconds=0.05)
    window = ImageJakduWindow(process=processor)
    qtbot.addWidget(window)
    window.show()

    window.set_source_files((PureWindowsPath(r"C:\images\first.png"),))
    window.set_output_folder(PureWindowsPath(str(tmp_path)))

    window.process_button.click()
    qtbot.waitUntil(lambda: window.progress_bar.value() > 0, timeout=1000)

    window.cancel_button.click()
    qtbot.waitUntil(lambda: window.status_label.text() == "Processing cancelled.", timeout=1000)

    assert (tmp_path / "result_1.png").exists() is False
    assert window.process_button.isEnabled()
    assert not window.cancel_button.isEnabled()


def test_stale_job_signal_does_not_overwrite_newer_status(qtbot: QtBot, tmp_path: Path) -> None:
    _ = QApplication.instance() or QApplication([])

    processor = ProgressCaptureProcessor(output_dir=tmp_path, delay_seconds=0.05)
    window = ImageJakduWindow(process=processor)
    qtbot.addWidget(window)
    window.show()
    window.set_source_files((PureWindowsPath(r"C:\images\first.png"),))
    window.set_output_folder(PureWindowsPath(str(tmp_path)))

    window.process_button.click()
    qtbot.waitUntil(lambda: window.status_label.text() == "Processing...", timeout=1000)
    window.status_label.setText("Processing current job")
    window.progress_bar.setValue(44)

    window.on_completed(0, (PureWindowsPath(r"C:\old\result.png"),))
    window.on_progress(0, 3, 3, "old job complete")
    window.on_failed(0, "old failure")
    window.on_cancelled(0)

    assert window.status_label.text() == "Processing current job"
    assert window.progress_bar.value() == 44
    window.cancel_button.click()
    qtbot.waitUntil(lambda: window.status_label.text() == "Processing cancelled.", timeout=1000)


def test_worker_failure_updates_status_and_recovers_to_idle(
    qtbot: QtBot,
    tmp_path: Path,
) -> None:
    _ = QApplication.instance() or QApplication([])

    def fail_process(
        _request: GuiProcessRequest,
        _report_progress: ProgressReporter,
        _is_cancel_requested: Callable[[], bool],
    ) -> tuple[PureWindowsPath, ...]:
        msg = "model failed"
        raise RuntimeError(msg)

    window = ImageJakduWindow(process=fail_process)
    qtbot.addWidget(window)
    window.show()
    window.set_source_files((PureWindowsPath(r"C:\images\first.png"),))
    window.set_output_folder(PureWindowsPath(str(tmp_path)))

    window.process_button.click()
    qtbot.waitUntil(lambda: window.status_label.text() == "Processing failed.", timeout=1000)

    assert window.validation_label.text() == "model failed"
    assert window.progress_bar.value() == 0
    assert window.process_button.isEnabled()
    assert not window.cancel_button.isEnabled()


def test_start_without_ready_request_reports_validation_error(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])

    window = ImageJakduWindow()
    qtbot.addWidget(window)
    window.show()

    window.start_processing()

    assert window.status_label.text() == "Select images and an output folder before processing."
    assert window.validation_label.text() == "Select at least one image and an output folder."
    assert not window.process_button.isEnabled()
