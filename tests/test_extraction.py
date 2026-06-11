from __future__ import annotations

import sys
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

from image_jakdu.extraction import (
    ExtractionUnavailableError,
    ForegroundMask,
    ModelExtractionService,
    RembgMaskProvider,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class FakeMaskProvider:
    mask: ForegroundMask

    def extract_mask(self, image_bytes: bytes) -> ForegroundMask:
        if image_bytes == b"":
            message = "image bytes should not be empty"
            raise AssertionError(message)
        return self.mask


@dataclass(frozen=True, slots=True)
class UnavailableMaskProvider:
    def extract_mask(self, image_bytes: bytes) -> ForegroundMask:
        if image_bytes != b"":
            raise ExtractionUnavailableError(reason="rembg model unavailable")
        message = "image bytes should not be empty"
        raise AssertionError(message)


def test_model_mask_produces_crop_box() -> None:
    service = ModelExtractionService(
        provider=FakeMaskProvider(
            mask=ForegroundMask(
                width=6,
                height=5,
                alpha=(
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    255,
                    255,
                    0,
                    0,
                    0,
                    0,
                    255,
                    255,
                    255,
                    0,
                    0,
                    0,
                    0,
                    255,
                    255,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ),
            ),
        ),
    )

    result = service.extract_crop_box(image_bytes=b"png-bytes")

    assert result.crop_box == (1, 1, 4, 4)
    assert result.fallback_reason is None


def test_model_unavailable_returns_fallback_reason() -> None:
    service = ModelExtractionService(provider=UnavailableMaskProvider())

    result = service.extract_crop_box(image_bytes=b"png-bytes")

    assert result.crop_box is None
    assert result.fallback_reason == "rembg model unavailable"


def test_rejects_empty_or_invalid_mask() -> None:
    with pytest.raises(ExtractionUnavailableError):
        _ = ForegroundMask(width=0, height=1, alpha=(0,))

    with pytest.raises(ExtractionUnavailableError):
        _ = ForegroundMask(width=2, height=2, alpha=(0, 255))


@dataclass(frozen=True, slots=True)
class FakeMaskImage:
    width: int
    height: int
    alpha: tuple[int, ...]

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    def convert(self, mode: str) -> FakeMaskImage:
        if mode != "L":
            message = "rembg mask must be converted to alpha channel"
            raise AssertionError(message)
        return self

    def getdata(self) -> Sequence[int]:
        return self.alpha


@dataclass(frozen=True, slots=True)
class FakeImageModule:
    image: FakeMaskImage

    def open(self, stream: object) -> FakeMaskImage:
        _ = stream
        return self.image


class FakeRembgModule(ModuleType):
    def remove(self, image_bytes: bytes, *, only_mask: bool) -> bytes:
        assert image_bytes == b"png-bytes"
        assert only_mask is True
        return b"mask-png"


class FakePillowImageModule(ModuleType):
    _fake_image_module: FakeImageModule

    def __init__(self, name: str, fake_image_module: FakeImageModule) -> None:
        super().__init__(name)
        self._fake_image_module = fake_image_module

    def open(self, stream: object) -> FakeMaskImage:
        return self._fake_image_module.open(stream)


def test_rembg_provider_uses_module_boundary_to_return_mask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_image_module = FakeImageModule(
        image=FakeMaskImage(
            width=3,
            height=2,
            alpha=(0, 255, 0, 0, 255, 255),
        ),
    )
    rembg_module = FakeRembgModule("rembg")
    image_module = FakePillowImageModule("PIL.Image", fake_image_module)
    monkeypatch.setitem(sys.modules, "rembg", rembg_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_module)

    provider = RembgMaskProvider()

    mask = provider.extract_mask(b"png-bytes")

    assert mask == ForegroundMask(
        width=3,
        height=2,
        alpha=(0, 255, 0, 0, 255, 255),
    )


def test_rembg_provider_reports_unavailable_when_dependency_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_spec(module_name: str, package: str | None = None) -> None:
        _ = (module_name, package)

    monkeypatch.delitem(sys.modules, "rembg", raising=False)
    monkeypatch.setattr("importlib.util.find_spec", missing_spec)
    provider = RembgMaskProvider()

    result = ModelExtractionService(provider=provider).extract_crop_box(b"png-bytes")

    assert result.crop_box is None
    assert result.fallback_reason == "rembg is not installed"
