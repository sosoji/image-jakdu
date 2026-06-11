# Image Jakdu

Image Jakdu is a Windows-first Python GUI app for splitting saved images into
count-grid, pixel-size, auto-detected, or model-assisted crops.

## Current Run Path

Install dependencies and run tests from the project root:

```powershell
uv run --extra dev python -m pytest -q
uv run --extra dev python -m ruff check .
uv run --extra dev python -m basedpyright
```

Run the GUI from a desktop Windows session with the project environment active.
Headless CI can exercise the GUI state with:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run --extra dev python -m pytest tests/test_gui_state.py -q
```

See `docs/windows-setup.md` for Docker Desktop, Ollama, local model warmup,
rembg/U2-Net cache notes, troubleshooting, and the packaging path.

## Current Limitations

Windows installer is not built yet. The current packaging path is documented as
a PyInstaller plan, not a verified installer release.

The implementation is tracked in `.omo/plans/image-jakdu-image-splitter.md`.
