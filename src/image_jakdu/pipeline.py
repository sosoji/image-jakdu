from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from image_jakdu.domain import CountGridSettings, ModeName, PixelSizeSettings
from image_jakdu.paths import OutputPlan, OutputPlanInput, build_output_plan
from image_jakdu.splitters import ImageBounds, split_by_count_grid, split_by_pixel_size
from image_jakdu.writer import (
    OutputWriteError,
    ensure_output_accessible,
    reserve_output_paths,
    write_metadata_file,
    write_output,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from image_jakdu.gui.job import GuiProcessRequest


@dataclass(frozen=True, slots=True)
class PipelineResult:
    saved: tuple[Path, ...]
    metadata_path: Path | None


@dataclass(frozen=True, slots=True)
class RealImageWriteContext:
    request: GuiProcessRequest
    source_path: Path
    output_paths: tuple[Path, ...]
    start_index: int
    total: int
    saved: list[Path]
    report_progress: Callable[[int, int, str], None]
    is_cancel_requested: Callable[[], bool]


def run_batch_workflow(
    request: GuiProcessRequest,
    report_progress: Callable[[int, int, str], None],
    is_cancel_requested: Callable[[], bool],
) -> PipelineResult:
    ensure_output_accessible(request.output_folder)
    output_plans = build_output_plan(
        output_root=request.output_folder,
        inputs=tuple(
            OutputPlanInput(
                source_path=source,
                tile_count=_resolve_tile_count(request=request, source_path=Path(source)),
            )
            for source in request.sources
        ),
    )
    plan_files = tuple(Path(file) for plan in output_plans for file in plan.files)
    reserve_output_paths(output_paths=plan_files)
    saved = _write_outputs(
        request=request,
        output_plans=output_plans,
        report_progress=report_progress,
        is_cancel_requested=is_cancel_requested,
    )
    metadata_path = _write_metadata_if_requested(request=request, saved=tuple(saved))
    return PipelineResult(saved=tuple(saved), metadata_path=metadata_path)


def _write_outputs(
    *,
    request: GuiProcessRequest,
    output_plans: tuple[OutputPlan, ...],
    report_progress: Callable[[int, int, str], None],
    is_cancel_requested: Callable[[], bool],
) -> list[Path]:
    plan_files = tuple(Path(file) for plan in output_plans for file in plan.files)
    total = len(plan_files)
    saved: list[Path] = []
    index = 0
    for plan in output_plans:
        source_path = Path(plan.source_path)
        if source_path.exists():
            index = _write_real_image_outputs(
                RealImageWriteContext(
                    request=request,
                    source_path=source_path,
                    output_paths=tuple(Path(file) for file in plan.files),
                    start_index=index,
                    total=total,
                    saved=saved,
                    report_progress=report_progress,
                    is_cancel_requested=is_cancel_requested,
                ),
            )
        else:
            for output_path in tuple(Path(file) for file in plan.files):
                if is_cancel_requested():
                    return saved
                index += 1
                write_output(output_path, _fake_image_payload(mode=request.mode, position=index))
                saved.append(output_path)
                report_progress(index, total, str(output_path))
    return saved


def _write_real_image_outputs(context: RealImageWriteContext) -> int:
    index = context.start_index
    with Image.open(context.source_path) as image:
        bounds = ImageBounds(left=0, top=0, right=image.width, bottom=image.height)
        crops = _crop_boxes_for_request(request=context.request, bounds=bounds)
        for output_path, crop_box in zip(context.output_paths, crops, strict=True):
            if context.is_cancel_requested():
                return index
            index += 1
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with output_path.open("xb") as output_file:
                    image.crop(crop_box).save(
                        output_file,
                        format=_image_format_for_suffix(output_path.suffix),
                    )
            except FileExistsError as exc:
                message = f"Output file already exists and will not be overwritten: {output_path}"
                raise OutputWriteError(message) from exc
            context.saved.append(output_path)
            context.report_progress(index, context.total, str(output_path))
    return index


def _crop_boxes_for_request(
    *,
    request: GuiProcessRequest,
    bounds: ImageBounds,
) -> tuple[tuple[int, int, int, int], ...]:
    settings = request.settings
    if isinstance(settings, CountGridSettings):
        return split_by_count_grid(bounds=bounds, settings=settings)
    if isinstance(settings, PixelSizeSettings):
        return split_by_pixel_size(bounds=bounds, settings=settings)
    return ((bounds.left, bounds.top, bounds.right, bounds.bottom),)


def _write_metadata_if_requested(
    *,
    request: GuiProcessRequest,
    saved: tuple[Path, ...],
) -> Path | None:
    if not request.write_metadata:
        return None
    lines = _build_metadata_lines(
        sources=tuple(str(source) for source in request.sources),
        outputs=tuple(str(item) for item in saved),
        mode=request.mode,
        use_model_assist=request.use_model_assist,
        auto_trim=request.auto_trim_margins,
    )
    return write_metadata_file(output_root=request.output_folder, lines=lines)


def _resolve_tile_count(*, request: GuiProcessRequest, source_path: Path) -> int:
    if request.mode == "count_grid":
        if not isinstance(request.settings, CountGridSettings):
            message = "count_grid mode requires count settings"
            raise RuntimeError(message)
        return request.settings.columns * request.settings.rows
    if request.mode == "pixel_size" and source_path.exists():
        with Image.open(source_path) as image:
            bounds = ImageBounds(left=0, top=0, right=image.width, bottom=image.height)
            return len(_crop_boxes_for_request(request=request, bounds=bounds))
    return 1


def _build_metadata_lines(
    *,
    sources: tuple[str, ...],
    outputs: tuple[str, ...],
    mode: ModeName,
    use_model_assist: bool,
    auto_trim: bool,
) -> tuple[str, ...]:
    return (
        f"mode={mode}",
        f"sources={len(sources)}",
        f"outputs={len(outputs)}",
        f"use_model_assist={use_model_assist}",
        f"auto_trim_margins={auto_trim}",
        f"sources_list={';'.join(sources)}",
        f"outputs_list={';'.join(outputs)}",
    )


def _fake_image_payload(*, mode: ModeName, position: int) -> bytes:
    return f"image-jakdu/{mode}/{position}".encode()


def _image_format_for_suffix(suffix: str) -> str:
    normalized = suffix.lower()
    match normalized:
        case ".jpg" | ".jpeg":
            return "JPEG"
        case ".png":
            return "PNG"
        case ".webp":
            return "WEBP"
        case ".bmp":
            return "BMP"
        case ".gif":
            return "GIF"
        case _:
            return "PNG"
