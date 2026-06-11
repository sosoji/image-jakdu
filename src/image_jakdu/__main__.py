from __future__ import annotations

from PySide6.QtWidgets import QApplication

from image_jakdu.gui import ImageJakduWindow


def main() -> int:
    app = QApplication([])
    window = ImageJakduWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
