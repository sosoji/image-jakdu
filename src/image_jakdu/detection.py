from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from image_jakdu.domain import ValidationFailure

if TYPE_CHECKING:
    from image_jakdu.extraction import ExtractionResult
    from image_jakdu.splitters import CropBox


@dataclass(frozen=True, slots=True)
class BinaryImage:
    width: int
    height: int
    alpha: tuple[int, ...]
    intensity: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.width <= 0:
            message = "image width must be positive"
            raise ValidationFailure(message)
        if self.height <= 0:
            message = "image height must be positive"
            raise ValidationFailure(message)
        expected_length = self.width * self.height
        if len(self.alpha) != expected_length:
            message = "alpha length must match dimensions"
            raise ValidationFailure(message)
        if len(self.intensity) != expected_length:
            message = "intensity length must match dimensions"
            raise ValidationFailure(message)


@dataclass(frozen=True, slots=True)
class DetectionCandidate:
    crop_box: CropBox
    source: str


class CropExtractionService(Protocol):
    def extract_crop_box(self, image_bytes: bytes) -> ExtractionResult: ...


@dataclass(frozen=True, slots=True)
class PixelPosition:
    x: int
    y: int


def trim_uniform_margin(
    *,
    image: BinaryImage,
    background_intensity: int,
    tolerance: int,
) -> CropBox | None:
    return detect_content_bounds(
        image=image,
        background_intensity=background_intensity,
        tolerance=tolerance,
    )


def detect_content_bounds(
    *,
    image: BinaryImage,
    background_intensity: int,
    tolerance: int,
) -> CropBox | None:
    active_x: list[int] = []
    active_y: list[int] = []

    for index, alpha_value in enumerate(image.alpha):
        intensity = image.intensity[index]
        if alpha_value <= 0:
            continue
        if abs(intensity - background_intensity) <= tolerance:
            continue
        y, x = divmod(index, image.width)
        active_x.append(x)
        active_y.append(y)

    if len(active_x) == 0:
        return None

    return (min(active_x), min(active_y), max(active_x) + 1, max(active_y) + 1)


def detect_separated_region_candidates(
    *,
    image: BinaryImage,
    background_intensity: int,
    tolerance: int,
) -> tuple[DetectionCandidate, ...]:
    candidates: list[DetectionCandidate] = []
    visited: set[int] = set()

    for index in range(image.width * image.height):
        if index in visited:
            continue
        if not _is_foreground_pixel(
            image=image,
            index=index,
            background_intensity=background_intensity,
            tolerance=tolerance,
        ):
            visited.add(index)
            continue

        region = _collect_region(
            image=image,
            start_index=index,
            background_intensity=background_intensity,
            tolerance=tolerance,
            visited=visited,
        )
        candidates.append(
            DetectionCandidate(
                crop_box=_bounds_for_region(region=region),
                source="deterministic",
            ),
        )

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (candidate.crop_box[1], candidate.crop_box[0]),
        ),
    )


def model_candidate_from_extraction(
    *,
    service: CropExtractionService,
    image_bytes: bytes,
) -> DetectionCandidate | None:
    result = service.extract_crop_box(image_bytes)
    if result.crop_box is None:
        return None
    return DetectionCandidate(crop_box=result.crop_box, source="model")


def _is_foreground_pixel(
    *,
    image: BinaryImage,
    index: int,
    background_intensity: int,
    tolerance: int,
) -> bool:
    alpha_value = image.alpha[index]
    intensity = image.intensity[index]
    return alpha_value > 0 and abs(intensity - background_intensity) > tolerance


def _collect_region(
    *,
    image: BinaryImage,
    start_index: int,
    background_intensity: int,
    tolerance: int,
    visited: set[int],
) -> tuple[PixelPosition, ...]:
    pending = [start_index]
    region: list[PixelPosition] = []

    while len(pending) > 0:
        index = pending.pop()
        if index in visited:
            continue
        visited.add(index)
        if not _is_foreground_pixel(
            image=image,
            index=index,
            background_intensity=background_intensity,
            tolerance=tolerance,
        ):
            continue

        y, x = divmod(index, image.width)
        region.append(PixelPosition(x=x, y=y))
        pending.extend(_neighbor_indexes(image=image, position=PixelPosition(x=x, y=y)))

    return tuple(region)


def _neighbor_indexes(*, image: BinaryImage, position: PixelPosition) -> tuple[int, ...]:
    neighbors: list[int] = []
    if position.x > 0:
        neighbors.append((position.y * image.width) + position.x - 1)
    if position.x < image.width - 1:
        neighbors.append((position.y * image.width) + position.x + 1)
    if position.y > 0:
        neighbors.append(((position.y - 1) * image.width) + position.x)
    if position.y < image.height - 1:
        neighbors.append(((position.y + 1) * image.width) + position.x)
    return tuple(neighbors)


def _bounds_for_region(*, region: tuple[PixelPosition, ...]) -> CropBox:
    left = min(position.x for position in region)
    top = min(position.y for position in region)
    right = max(position.x for position in region) + 1
    bottom = max(position.y for position in region) + 1
    return (left, top, right, bottom)
