from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from image_jakdu.detection import BinaryImage
    from image_jakdu.splitters import CropBox


def background_ratio(
    *,
    image: BinaryImage,
    crop_box: CropBox,
    background_intensity: int,
    tolerance: int,
) -> float:
    total_pixels = area(crop_box)
    if total_pixels == 0:
        return 1.0

    background_pixels = 0
    for y in range(crop_box[1], crop_box[3]):
        for x in range(crop_box[0], crop_box[2]):
            index = (y * image.width) + x
            if image.alpha[index] <= 0:
                background_pixels += 1
                continue
            if abs(image.intensity[index] - background_intensity) <= tolerance:
                background_pixels += 1
    return background_pixels / total_pixels


def area(crop_box: CropBox) -> int:
    return max(0, crop_box[2] - crop_box[0]) * max(0, crop_box[3] - crop_box[1])


def duplicates_previous(
    crop_box: CropBox,
    previous_boxes: list[CropBox],
    threshold: float,
) -> bool:
    for previous_box in previous_boxes:
        if overlap_ratio(crop_box, previous_box) >= threshold:
            return True
    return False


def overlap_ratio(first: CropBox, second: CropBox) -> float:
    intersection = intersection_area(first, second)
    smaller_area = min(area(first), area(second))
    if smaller_area == 0:
        return 0.0
    return intersection / smaller_area


def intersection_area(first: CropBox, second: CropBox) -> int:
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    return max(0, right - left) * max(0, bottom - top)
