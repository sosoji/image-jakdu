from __future__ import annotations

from pathlib import Path


def test_windows_docs_include_runtime_model_and_packaging_paths() -> None:
    windows_doc = Path("docs/windows-setup.md").read_text()
    readme = Path("README.md").read_text()

    required_windows_terms = (
        "uv run",
        "QT_QPA_PLATFORM",
        "Docker Desktop",
        "qwen2.5:1.5b-instruct",
        "rembg",
        "U2-Net",
        "PyInstaller",
        "manual bypass",
        "http://localhost:11434",
    )

    for term in required_windows_terms:
        assert term in windows_doc

    assert "docs/windows-setup.md" in readme
    assert "uv run --extra dev python" in readme
    assert "ImageJakdu-0.1.2-windows-installer.exe" in readme
    assert "ImageJakdu-0.1.2-macos.dmg" in readme
