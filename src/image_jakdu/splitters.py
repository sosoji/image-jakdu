from __future__ import annotations

from dataclasses import dataclass

from image_jakdu.domain import CountGridSettings, PixelSizeSettings, ValidationFailure

CropBox = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class ImageBounds:
    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self) -> None:
        if self.right <= self.left:
            message = "bounds width must be positive"
            raise ValidationFailure(message)
        if self.bottom <= self.top:
            message = "bounds height must be positive"
            raise ValidationFailure(message)

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def split_by_count_grid(*, bounds: ImageBounds, settings: CountGridSettings) -> tuple[CropBox, ...]:
    crops: list[CropBox] = []
    for row in range(settings.rows):
        top = bounds.top + (bounds.height * row // settings.rows)
        bottom = bounds.top + (bounds.height * (row + 1) // settings.rows)
        for column in range(settings.columns):
            left = bounds.left + (bounds.width * column // settings.columns)
            right = bounds.left + (bounds.width * (column + 1) // settings.columns)
            crops.append((left, top, right, bottom))
    return tuple(crops)


def split_by_pixel_size(*, bounds: ImageBounds, settings: PixelSizeSettings) -> tuple[CropBox, ...]:
    crops: list[CropBox] = []
    y = bounds.top
    while y < bounds.bottom:
        bottom = min(y + settings.tile_height, bounds.bottom)
        x = bounds.left
        while x < bounds.right:
            right = min(x + settings.tile_width, bounds.right)
            crops.append((x, y, right, bottom))
            x += settings.tile_width
        y += settings.tile_height
    return tuple(crops)
