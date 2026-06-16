from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_entrypoint_is_packager_ready() -> None:
    # Given: the project metadata drives PyInstaller and installed launchers.
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    # When: release packaging looks for the GUI script entrypoint.
    expected_entrypoint = 'image-jakdu = "image_jakdu.__main__:main"'
    expected_packager = '"pyinstaller>=6.11.0"'

    # Then: the release has a stable GUI command and bundled packager.
    assert expected_entrypoint in pyproject
    assert expected_packager in pyproject
    assert (ROOT / "src/image_jakdu/__main__.py").is_file()


def test_release_workflow_builds_windows_installer_and_macos_dmg() -> None:
    # Given: GitHub release builds are the source of cross-platform artifacts.
    workflow_path = ROOT / ".github/workflows/release.yml"

    # When: the release workflow is parsed.
    workflow = workflow_path.read_text(encoding="utf-8")

    # Then: native runners build the expected user-downloadable files.
    assert '      - "v*"' in workflow
    assert "build-windows:" in workflow
    assert "runs-on: windows-latest" in workflow
    assert "build-macos:" in workflow
    assert "runs-on: macos-latest" in workflow
    assert "ImageJakdu-0.1.2-windows.exe" in workflow
    assert "ImageJakdu-0.1.2-windows-installer.exe" in workflow
    assert "ImageJakdu-0.1.2-macos.dmg" in workflow


def test_windows_installer_script_packages_pyinstaller_exe() -> None:
    # Given: Windows users need an automatic installer, not only a raw exe.
    installer_path = ROOT / "packaging/windows/image-jakdu.nsi"

    # When: the NSIS script is inspected.
    installer = installer_path.read_text(encoding="utf-8")

    # Then: it installs the PyInstaller executable and creates shortcuts.
    assert 'OutFile "..\\..\\dist\\ImageJakdu-0.1.2-windows-installer.exe"' in installer
    assert '!define SOURCE_EXE "..\\..\\dist\\ImageJakdu.exe"' in installer
    assert 'File "${SOURCE_EXE}"' in installer
    assert "CreateShortCut" in installer


def test_windows_installer_installs_runtime_prerequisite() -> None:
    # Given: Windows users should not manually install runtime dependencies.
    installer_path = ROOT / "packaging/windows/image-jakdu.nsi"

    # When: the NSIS script is inspected.
    installer = installer_path.read_text(encoding="utf-8")

    # Then: the installer elevates and installs the VC++ runtime before app files.
    assert "RequestExecutionLevel admin" in installer
    assert "vc_redist.x64.exe" in installer
    assert "/install /quiet /norestart" in installer
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "https://aka.ms/vs/17/release/vc_redist.x64.exe" in workflow
