from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from importlib import import_module
from io import BytesIO
from typing import TYPE_CHECKING, Protocol, TypeGuard

from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class ExtractionUnavailableError(Exception):
    reason: str

    @override
    def __str__(self) -> str:
        return self.reason


@dataclass(frozen=True, slots=True)
class ForegroundMask:
    width: int
    height: int
    alpha: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.width <= 0:
            message = "mask width must be positive"
            raise ExtractionUnavailableError(reason=message)
        if self.height <= 0:
            message = "mask height must be positive"
            raise ExtractionUnavailableError(reason=message)
        expected_length = self.width * self.height
        if len(self.alpha) != expected_length:
            message = "mask alpha length must match dimensions"
            raise ExtractionUnavailableError(reason=message)


class MaskProvider(Protocol):
    def extract_mask(self, image_bytes: bytes) -> ForegroundMask: ...


class RembgRemove(Protocol):
    def __call__(self, image_bytes: bytes, *, only_mask: bool) -> bytes: ...


class MaskImage(Protocol):
    @property
    def size(self) -> tuple[int, int]: ...

    def convert(self, mode: str) -> MaskImage: ...

    def getdata(self) -> Sequence[int]: ...


class MaskImageModule(Protocol):
    def open(self, stream: BytesIO) -> MaskImage: ...


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    crop_box: tuple[int, int, int, int] | None
    fallback_reason: str | None


@dataclass(frozen=True, slots=True)
class ModelExtractionService:
    provider: MaskProvider

    def extract_crop_box(self, image_bytes: bytes) -> ExtractionResult:
        try:
            mask = self.provider.extract_mask(image_bytes)
        except ExtractionUnavailableError as exc:
            return ExtractionResult(crop_box=None, fallback_reason=exc.reason)

        crop_box = _crop_box_from_mask(mask)
        if crop_box is None:
            return ExtractionResult(crop_box=None, fallback_reason="foreground mask is empty")
        return ExtractionResult(crop_box=crop_box, fallback_reason=None)


@dataclass(frozen=True, slots=True)
class RembgMaskProvider:
    def is_available(self) -> bool:
        return _is_module_available("rembg") and _is_module_available("PIL.Image")

    def extract_mask(self, image_bytes: bytes) -> ForegroundMask:
        if len(image_bytes) == 0:
            raise ExtractionUnavailableError(reason="image bytes should not be empty")
        if not _is_module_available("rembg"):
            raise ExtractionUnavailableError(reason="rembg is not installed")
        if not _is_module_available("PIL.Image"):
            raise ExtractionUnavailableError(reason="Pillow is not installed")

        remove = _load_rembg_remove()
        image_module = _load_mask_image_module()
        mask_bytes = remove(image_bytes, only_mask=True)
        mask_image = image_module.open(BytesIO(mask_bytes)).convert("L")
        width, height = mask_image.size
        return ForegroundMask(width=width, height=height, alpha=tuple(mask_image.getdata()))


def _crop_box_from_mask(mask: ForegroundMask) -> tuple[int, int, int, int] | None:
    active_x: list[int] = []
    active_y: list[int] = []

    for index, alpha_value in enumerate(mask.alpha):
        if alpha_value <= 0:
            continue
        y, x = divmod(index, mask.width)
        active_x.append(x)
        active_y.append(y)

    if len(active_x) == 0:
        return None

    left = min(active_x)
    top = min(active_y)
    right = max(active_x) + 1
    bottom = max(active_y) + 1
    return (left, top, right, bottom)


def _is_module_available(module_name: str) -> bool:
    if module_name in sys.modules:
        return True
    return importlib.util.find_spec(module_name) is not None


def _load_rembg_remove() -> RembgRemove:
    module = import_module("rembg")
    remove = getattr(module, "remove", None)
    if not _is_rembg_remove(remove):
        raise ExtractionUnavailableError(reason="rembg remove function is unavailable")
    return remove


def _load_mask_image_module() -> MaskImageModule:
    module = import_module("PIL.Image")
    if not _is_mask_image_module(module):
        raise ExtractionUnavailableError(reason="Pillow image loader is unavailable")
    return module


def _is_rembg_remove(value: object) -> TypeGuard[RembgRemove]:
    return callable(value)


def _is_mask_image_module(value: object) -> TypeGuard[MaskImageModule]:
    return hasattr(value, "open")
