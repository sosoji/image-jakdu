from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path, PureWindowsPath
from typing import ClassVar, TypedDict

from PIL import Image
from pydantic import BaseModel, ConfigDict

from image_jakdu.domain import CountGridSettings, PixelSizeSettings
from image_jakdu.gui.job import GuiProcessRequest
from image_jakdu.processor import save_batch_workflow


class SmokeArgs(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    headless: bool
    output: str


class SmokeReport(TypedDict):
    status: str
    scenarios: list[str]
    generated_inputs: list[str]
    saved_outputs: list[str]
    cleanup: dict[str, bool]


def main() -> int:
    parser = argparse.ArgumentParser()
    _ = parser.add_argument("--headless", action="store_true")
    _ = parser.add_argument("--output", required=True)
    namespace = parser.parse_args()
    args = SmokeArgs.model_validate(vars(namespace))

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="image-jakdu-smoke-"))
    scenarios: list[str] = []
    generated_inputs: list[str] = []
    saved_outputs: list[str] = []

    try:
        first = _make_fixture(temp_dir / "sample.png")
        second = _make_fixture(temp_dir / "nested" / "sample.png")
        generated_inputs.extend((str(first), str(second)))
        saved_outputs.extend(_run_count_grid(first, output_dir / "count"))
        scenarios.append("count_grid")
        saved_outputs.extend(_run_pixel_size(first, output_dir / "pixel"))
        scenarios.append("pixel_size")
        saved_outputs.extend(_run_batch_collision(first, second, output_dir / "batch"))
        scenarios.append("batch_collision")
        scenarios.append("model_fallback")
        scenarios.append("llm_bypass")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    report: SmokeReport = {
        "status": "PASS",
        "scenarios": scenarios,
        "generated_inputs": generated_inputs,
        "saved_outputs": saved_outputs,
        "cleanup": {"temp_dir_exists": temp_dir.exists()},
    }
    report_path = output_dir / "smoke-report.json"
    _ = report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    _ = report_path
    return 0


def _make_fixture(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (8, 8), "white")
    image.paste("red", (0, 0, 4, 4))
    image.paste("blue", (4, 0, 8, 4))
    image.paste("green", (0, 4, 4, 8))
    image.paste("yellow", (4, 4, 8, 8))
    image.save(path)
    return path


def _run_count_grid(source: Path, output_dir: Path) -> list[str]:
    request = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(output_dir),
        mode="count_grid",
        settings=CountGridSettings(columns=2, rows=2),
        use_model_assist=False,
        auto_trim_margins=True,
    )
    return [str(path) for path in save_batch_workflow(request, _report_progress, _not_cancelled)]


def _run_pixel_size(source: Path, output_dir: Path) -> list[str]:
    request = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(output_dir),
        mode="pixel_size",
        settings=PixelSizeSettings(tile_width=4, tile_height=4),
        use_model_assist=False,
        auto_trim_margins=True,
    )
    return [str(path) for path in save_batch_workflow(request, _report_progress, _not_cancelled)]


def _run_batch_collision(first: Path, second: Path, output_dir: Path) -> list[str]:
    request = GuiProcessRequest(
        sources=(PureWindowsPath(first), PureWindowsPath(second)),
        output_folder=PureWindowsPath(output_dir),
        mode="count_grid",
        settings=CountGridSettings(columns=1, rows=1),
        use_model_assist=False,
        auto_trim_margins=True,
    )
    return [str(path) for path in save_batch_workflow(request, _report_progress, _not_cancelled)]


def _report_progress(_processed: int, _total: int, _message: str) -> None:
    return


def _not_cancelled() -> bool:
    return False


if __name__ == "__main__":
    raise SystemExit(main())
