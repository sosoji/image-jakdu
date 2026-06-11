from __future__ import annotations

from pathlib import Path, PureWindowsPath
from typing import Final

from PySide6.QtWidgets import QApplication

from image_jakdu.gui.main_window import ImageJakduWindow

OUTPUT: Final = Path(".omo/evidence/task-10-gui-state.png")


def main() -> int:
    app = QApplication.instance() or QApplication([])
    window = ImageJakduWindow()
    window.set_source_files(
        (PureWindowsPath("C:/images/first.png"), PureWindowsPath("C:/images/second.png")),
    )
    window.set_output_folder(PureWindowsPath("C:/results/이미지 작두"))
    window.intent_text.setPlainText("이미지를 4 x 3으로 잘라줘")
    window.apply_intent_json(
        (
            '{"mode":"count_grid","columns":4,"rows":3,'
            '"use_model_assist":true,"auto_trim_margins":true}'
        ),
    )
    window.resize(760, 520)
    window.show()
    _ = app.processEvents()
    pixmap = window.grab()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(OUTPUT)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
