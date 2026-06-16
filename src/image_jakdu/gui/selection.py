from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QWidget

SourcePicker = Callable[[QWidget], tuple[str, ...]]
OutputPicker = Callable[[QWidget], str]
IntentProvider = Callable[[str], str]
