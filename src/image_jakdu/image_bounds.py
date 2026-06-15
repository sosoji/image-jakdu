from __future__ import annotations

from typing import TYPE_CHECKING

from image_jakdu.detection import BinaryImage, trim_uniform_margin
from image_jakdu.domain import DEFAULT_TOLERANCE
from image_jakdu.extraction import ModelExtractionService, RembgMaskProvider
from image_jakdu.splitters import ImageBounds

if TYPE_CHECKING:
    from pathlib import Path

    from PIL import Image

    from image_jakdu.gui.job import GuiProcessRequest


def bounds_for_request(
    *,
    request: GuiProcessRequest,
    image: Image.Image,
    source_path: Path,
) -> ImageBounds:
    full_bounds = ImageBounds(left=0, top=0, right=image.width, bottom=image.height)
    model_bounds = _model_bounds_if_available(request=request, source_path=source_path)
    if model_bounds is not None:
        return model_bounds
    if request.auto_trim_margins:
        trim_bounds = _trim_bounds_if_available(image=image)
        if trim_bounds is not None:
            return trim_bounds
    return full_bounds


def _model_bounds_if_available(
    *,
    request: GuiProcessRequest,
    source_path: Path,
) -> ImageBounds | None:
    if not request.use_model_assist and request.mode != "model_assisted":
        return None

    result = ModelExtractionService(provider=RembgMaskProvider()).extract_crop_box(
        source_path.read_bytes(),
    )
    if result.crop_box is None:
        return None
    left, top, right, bottom = result.crop_box
    return ImageBounds(left=left, top=top, right=right, bottom=bottom)


def _trim_bounds_if_available(*, image: Image.Image) -> ImageBounds | None:
    binary_image = _binary_image_from_image(image)
    background_intensity = _corner_background_intensity(binary_image)
    if background_intensity is None:
        return None
    trim_box = trim_uniform_margin(
        image=binary_image,
        background_intensity=background_intensity,
        tolerance=DEFAULT_TOLERANCE,
    )
    if trim_box is None:
        return None
    left, top, right, bottom = trim_box
    return ImageBounds(left=left, top=top, right=right, bottom=bottom)


def _binary_image_from_image(image: Image.Image) -> BinaryImage:
    rgba_image = image.convert("RGBA")
    raw_pixels = rgba_image.tobytes()
    return BinaryImage(
        width=rgba_image.width,
        height=rgba_image.height,
        alpha=tuple(raw_pixels[index + 3] for index in range(0, len(raw_pixels), 4)),
        intensity=tuple(
            (raw_pixels[index] + raw_pixels[index + 1] + raw_pixels[index + 2]) // 3
            for index in range(0, len(raw_pixels), 4)
        ),
    )


def _corner_background_intensity(image: BinaryImage) -> int | None:
    corner_indexes = (
        0,
        image.width - 1,
        image.width * (image.height - 1),
        (image.width * image.height) - 1,
    )
    visible_intensities = tuple(
        image.intensity[index] for index in corner_indexes if image.alpha[index] > 0
    )
    if len(visible_intensities) == 0:
        return 0
    if max(visible_intensities) - min(visible_intensities) > DEFAULT_TOLERANCE:
        return None
    return sorted(visible_intensities)[len(visible_intensities) // 2]
