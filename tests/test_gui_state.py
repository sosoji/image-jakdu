from pathlib import PureWindowsPath
from typing import Final

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from image_jakdu.gui.main_window import ImageJakduWindow
from image_jakdu.gui.support import SOURCE_IMAGE_FILTER

INTENT_JSON: Final = (
    '{"mode":"count_grid","columns":4,"rows":3,"use_model_assist":true,"auto_trim_margins":true}'
)


def test_source_and_output_selection_enables_processing(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])
    window = ImageJakduWindow()
    qtbot.addWidget(window)
    window.show()

    window.set_source_files(
        (
            PureWindowsPath(r"C:\images\first.png"),
            PureWindowsPath(r"C:\images\second.png"),
        ),
    )
    window.set_output_folder(PureWindowsPath(r"C:\results\이미지 작두"))

    assert window.selected_sources == (
        PureWindowsPath(r"C:\images\first.png"),
        PureWindowsPath(r"C:\images\second.png"),
    )
    assert window.selected_output_folder == PureWindowsPath(r"C:\results\이미지 작두")
    assert window.process_button.isEnabled()


def test_mode_switch_shows_relevant_controls(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])
    window = ImageJakduWindow()
    qtbot.addWidget(window)
    window.show()

    window.mode_selector.setCurrentText("Pixel size")

    assert window.count_controls.isVisible() is False
    assert window.pixel_controls.isVisible() is True

    window.mode_selector.setCurrentText("Count grid")

    assert window.count_controls.isVisible() is True
    assert window.pixel_controls.isVisible() is False


def test_intent_json_populates_job_draft(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])
    window = ImageJakduWindow()
    qtbot.addWidget(window)
    window.show()

    window.intent_text.setPlainText("이미지를 4 x 3으로 잘라줘")
    window.apply_intent_json(
        INTENT_JSON,
    )

    assert window.mode_selector.currentText() == "Count grid"
    assert window.columns_input.value() == 4
    assert window.rows_input.value() == 3
    assert window.model_assist_checkbox.checkState() == Qt.CheckState.Checked
    assert window.auto_trim_checkbox.checkState() == Qt.CheckState.Checked


def test_picker_actions_update_state_and_status(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])

    def pick_sources(_parent: QWidget) -> tuple[str, ...]:
        return (r"C:\images\first.png", r"C:\images\second.png")

    def pick_output(_parent: QWidget) -> str:
        return r"C:\results\이미지 작두"

    window = ImageJakduWindow(source_picker=pick_sources, output_picker=pick_output)
    qtbot.addWidget(window)
    window.show()

    window.choose_source_files()
    window.choose_output_folder()

    assert window.selected_sources == (
        PureWindowsPath(r"C:\images\first.png"),
        PureWindowsPath(r"C:\images\second.png"),
    )
    assert window.selected_output_folder == PureWindowsPath(r"C:\results\이미지 작두")
    assert window.status_label.text() == "Ready to process 2 image(s)."
    assert window.process_button.isEnabled()


def test_source_picker_filter_includes_tiff_images() -> None:
    assert "*.png" in SOURCE_IMAGE_FILTER
    assert "*.jpg" in SOURCE_IMAGE_FILTER
    assert "*.jpeg" in SOURCE_IMAGE_FILTER
    assert "*.webp" in SOURCE_IMAGE_FILTER
    assert "*.bmp" in SOURCE_IMAGE_FILTER
    assert "*.tif" in SOURCE_IMAGE_FILTER
    assert "*.tiff" in SOURCE_IMAGE_FILTER


def test_intent_action_updates_preview_and_validation(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])
    window = ImageJakduWindow(intent_provider=lambda _text: INTENT_JSON)
    qtbot.addWidget(window)
    window.show()
    window.intent_text.setPlainText("이미지를 4 x 3으로 잘라줘")

    window.intent_button.click()

    assert window.columns_input.value() == 4
    assert window.rows_input.value() == 3
    assert window.status_label.text() == "Intent applied."
    assert "Count grid: 4 columns x 3 rows" in window.preview_label.text()


def test_invalid_intent_sets_validation_message(qtbot: QtBot) -> None:
    _ = QApplication.instance() or QApplication([])
    window = ImageJakduWindow(intent_provider=lambda _text: "not json")
    qtbot.addWidget(window)
    window.show()
    window.intent_text.setPlainText("bad")

    window.intent_button.click()

    assert window.status_label.text() == "Intent could not be applied."
    assert window.validation_label.text() != ""
