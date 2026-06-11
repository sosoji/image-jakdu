from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import PureWindowsPath

from image_jakdu.domain import ValidationFailure


@dataclass(frozen=True, slots=True)
class OutputPlanInput:
    source_path: PureWindowsPath
    tile_count: int

    def __post_init__(self) -> None:
        if self.tile_count <= 0:
            message = "tile_count must be a positive integer"
            raise ValidationFailure(message)


@dataclass(frozen=True, slots=True)
class OutputPlan:
    source_path: PureWindowsPath
    files: tuple[PureWindowsPath, ...]


def normalize_windows_path(raw_path: str) -> PureWindowsPath:
    return PureWindowsPath(raw_path)


def build_output_plan(
    *,
    output_root: PureWindowsPath,
    inputs: tuple[OutputPlanInput, ...],
) -> tuple[OutputPlan, ...]:
    basename_counts = Counter(_source_stem(item.source_path) for item in inputs)
    seen: dict[str, int] = {}
    plans: list[OutputPlan] = []

    for item in inputs:
        stem = _source_stem(item.source_path)
        seen_index = seen.get(stem, 0) + 1
        seen[stem] = seen_index
        parent = _output_parent(output_root, stem, seen_index, basename_counts[stem])
        files = tuple(
            parent / f"{stem}{tile_number}{item.source_path.suffix}"
            for tile_number in range(1, item.tile_count + 1)
        )
        plans.append(OutputPlan(source_path=item.source_path, files=files))

    return tuple(plans)


def _output_parent(
    output_root: PureWindowsPath,
    stem: str,
    seen_index: int,
    basename_count: int,
) -> PureWindowsPath:
    if basename_count == 1:
        return output_root
    if seen_index == 1:
        return output_root / stem
    return output_root / f"{stem}_{seen_index}"


def _source_stem(source_path: PureWindowsPath) -> str:
    stem = source_path.stem
    if stem == "":
        message = "source image must have a filename stem"
        raise ValidationFailure(message)
    return stem
