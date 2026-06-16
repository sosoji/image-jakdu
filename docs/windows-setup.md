# Windows Setup

Image Jakdu runs as a Windows Python GUI application with local model services.
Ordinary processing stays local and must not call cloud AI services.

## Prerequisites

- Windows 10 or Windows 11
- For normal users: download and run `ImageJakdu-0.1.2-windows-installer.exe`
- The installer includes the app and installs the Microsoft Visual C++ Runtime
- Python 3.11+ and `uv` are only needed for development from source
- Docker Desktop is only needed for the optional local Ollama intent model
- Enough disk space for Ollama and rembg/U2-Net model caches

## Install From Release

For ordinary Windows use, install from the GitHub release:

1. Download `ImageJakdu-0.1.2-windows-installer.exe`.
2. Run it and approve the Windows administrator prompt.
3. Launch Image Jakdu from the Start Menu or Desktop shortcut.

The installer places Image Jakdu under `Program Files`, creates shortcuts, and
installs the bundled Microsoft Visual C++ Runtime. Users do not need to install
Python, `uv`, or PySide6.

## Install And Test

For development from source, run these commands from the project directory in
PowerShell:

```powershell
uv run --extra dev python -m pytest -q
uv run --extra dev python -m ruff check .
uv run --extra dev python -m basedpyright
```

For headless GUI verification:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run --extra dev python -m pytest tests/test_gui_state.py -q
```

For a real desktop run, do not set `QT_QPA_PLATFORM=offscreen`; launch from a
normal Windows desktop session.

## Start The Local LLM Service

Start Ollama:

```powershell
docker compose up -d ollama
```

The local endpoint is:

```text
http://localhost:11434
```

Pull and warm the default intent model:

```powershell
docker exec -it image-jakdu-ollama-1 ollama pull qwen2.5:1.5b-instruct
docker exec -it image-jakdu-ollama-1 ollama run qwen2.5:1.5b-instruct
```

The intent model turns the user's Korean or English instruction into structured
JSON settings before processing starts. It does not receive image bytes.

## rembg And U2-Net Cache

Model-assisted image boundary detection uses the local rembg/U2-Net path when
available. The first run may download or populate a local U2-Net cache under the
current Windows user profile. Keep that cache local; do not configure cloud
model APIs for ordinary processing.

If rembg or U2-Net is unavailable, Image Jakdu reports a fallback reason and can
continue with deterministic trim, count, pixel, or manual settings.

## Manual Bypass

If Docker Desktop, Ollama, `qwen2.5:1.5b-instruct`, rembg, or U2-Net is
unavailable, use manual bypass. Manual bypass lets the GUI run with explicit
mode, count, pixel size, and auto/model settings without contacting the local
LLM service.

## Packaging Path

The Windows release packaging path is PyInstaller plus NSIS.

The GitHub release workflow builds `ImageJakdu.exe`, downloads the Microsoft
Visual C++ Runtime redistributable, bundles it into the NSIS installer, and
publishes both files to the release.

```powershell
uv run --extra dev pyinstaller --noconfirm --clean --windowed --onefile --name ImageJakdu src/image_jakdu/__main__.py
```

## Troubleshooting

- Docker Desktop not running: start Docker Desktop, then rerun
  `docker compose up -d ollama`.
- Windows asks for administrator approval: approve it so the bundled Microsoft
  Visual C++ Runtime can be installed.
- Ollama endpoint unavailable: check `http://localhost:11434/api/tags` and use
  manual bypass if needed.
- Slow first model run: warm `qwen2.5:1.5b-instruct` before starting a GUI job.
- Missing rembg/U2-Net cache: allow the local model cache to populate or use
  manual deterministic modes.
- GUI tests on CI: set `QT_QPA_PLATFORM=offscreen`; do not set it for real
  desktop use.
