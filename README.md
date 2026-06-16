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

## Korean Run Guide

### 1. 준비

Windows 10 또는 Windows 11에서 PowerShell을 열고 프로젝트 폴더로 이동합니다.

```powershell
cd C:\path\to\image-jakdu
```

필요한 도구:

- 일반 사용자: `ImageJakdu-0.1.2-windows-installer.exe`만 실행하면 됩니다.
- Python 3.11 이상과 `uv`는 소스에서 개발할 때만 필요합니다.
- Docker Desktop은 로컬 LLM 기능을 사용할 때만 필요합니다.

### 일반 설치

GitHub Release에서 `ImageJakdu-0.1.2-windows-installer.exe`를 내려받아
실행합니다. 설치 중 Windows 관리자 권한 확인이 뜨면 승인하세요.

설치 파일은 Image Jakdu와 Microsoft Visual C++ Runtime을 함께 설치하고,
시작 메뉴와 바탕화면 바로가기를 만듭니다. 일반 사용자는 Python, `uv`,
PySide6를 따로 설치할 필요가 없습니다.

### 2. 개발 의존성 확인

소스에서 개발하거나 테스트할 때만 아래 명령을 실행합니다.

```powershell
uv run --extra dev python -m pytest -q
uv run --extra dev python -m ruff check .
uv run --extra dev python -m basedpyright
uv run --extra dev python -m pyright
```

### 3. 로컬 LLM 실행

사용자 의도를 한국어 또는 영어로 입력받아 구조화하려면 Ollama 컨테이너를 먼저
실행합니다.

```powershell
docker compose up -d ollama
docker exec -it image-jakdu-ollama-1 ollama pull qwen2.5:1.5b-instruct
```

LLM 없이도 수동 모드로 이미지 경로, 저장 폴더, 가로 분할 수, 세로 분할 수를
직접 지정해서 사용할 수 있습니다.

### 4. GUI 실행

현재는 완성된 Windows 설치 파일이 아니라 개발 실행 방식입니다. 실제 데스크톱
환경에서는 `QT_QPA_PLATFORM=offscreen`을 설정하지 마세요.

```powershell
uv run --extra dev python -c "from PySide6.QtWidgets import QApplication; from image_jakdu.gui import ImageJakduWindow; app = QApplication([]); window = ImageJakduWindow(); window.show(); raise SystemExit(app.exec())"
```

GUI에서 할 일:

1. `Select images`로 자를 이미지 파일을 선택합니다.
2. `Select output folder`로 결과 이미지가 저장될 폴더를 선택합니다.
3. 모드를 선택합니다.
   - `Count grid`: 가로 개수와 세로 개수로 균일 분할
   - `Pixel size`: 타일의 가로/세로 픽셀 크기로 분할
   - `Auto detect`: 여백과 경계를 감지해서 자동 분할
   - `Model assisted`: 로컬 모델 보조 경계 감지 사용
4. 필요한 경우 `Auto trim margins`와 `Model assist`를 켭니다.
5. `Process`를 눌러 결과물을 저장합니다.

저장되는 파일 이름은 원본 이미지 이름을 기준으로 숫자가 붙습니다.

### 5. 스모크 QA 실행

실제 이미지 저장 동작을 빠르게 확인하려면 아래 명령을 사용합니다.

```powershell
uv run --extra dev python scripts/run_smoke_qa.py --headless --output .omo\evidence\manual-smoke
```

결과 폴더에는 분할된 샘플 이미지와 `smoke-report.json`이 생성됩니다.

### 6. 문제 해결

- Docker Desktop 오류: Docker Desktop을 먼저 켠 뒤 `docker compose up -d ollama`를 다시 실행합니다.
- GUI가 뜨지 않음: 실제 데스크톱 실행에서는 `QT_QPA_PLATFORM=offscreen`을 사용하지 않습니다.
- 첫 모델 실행이 느림: `qwen2.5:1.5b-instruct` 모델을 미리 pull 합니다.
- 자동 감지가 부족함: `Count grid` 또는 `Pixel size` 모드로 명시적으로 분할합니다.

## Release Artifacts

Release `v0.1.2` publishes native artifacts from GitHub Actions:

- `ImageJakdu-0.1.2-windows.exe`
- `ImageJakdu-0.1.2-windows-installer.exe`
- `ImageJakdu-0.1.2-macos-app.zip`
- `ImageJakdu-0.1.2-macos.dmg`

The implementation plan is tracked in `.omo/plans/image-jakdu-image-splitter.md`.
