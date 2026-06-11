from dataclasses import dataclass

import pytest

from image_jakdu.detection import (
    BinaryImage,
    DetectionCandidate,
    detect_content_bounds,
    detect_separated_region_candidates,
    model_candidate_from_extraction,
    trim_uniform_margin,
)
from image_jakdu.domain import ValidationFailure
from image_jakdu.extraction import ExtractionResult


@dataclass(frozen=True, slots=True)
class FakeExtractionService:
    result: ExtractionResult

    def extract_crop_box(self, image_bytes: bytes) -> ExtractionResult:
        if image_bytes == b"":
            message = "image bytes should not be empty"
            raise AssertionError(message)
        return self.result


def test_transparent_and_white_margin_trim_excludes_border() -> None:
    image = BinaryImage(
        width=5,
        height=4,
        alpha=(
            0,
            0,
            0,
            0,
            0,
            0,
            255,
            255,
            255,
            0,
            0,
            255,
            255,
            255,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
        intensity=(
            255,
            255,
            255,
            255,
            255,
            255,
            40,
            35,
            42,
            255,
            255,
            38,
            34,
            41,
            255,
            255,
            255,
            255,
            255,
            255,
        ),
    )

    bounds = trim_uniform_margin(image=image, background_intensity=255, tolerance=5)

    assert bounds == (1, 1, 4, 3)


def test_auto_detect_rejects_empty_background_regions() -> None:
    image = BinaryImage(
        width=3,
        height=3,
        alpha=(0, 0, 0, 0, 0, 0, 0, 0, 0),
        intensity=(255, 255, 255, 255, 255, 255, 255, 255, 255),
    )

    assert detect_content_bounds(image=image, background_intensity=255, tolerance=5) is None


def test_binary_image_rejects_zero_width() -> None:
    with pytest.raises(ValidationFailure, match="image width must be positive"):
        _ = BinaryImage(width=0, height=1, alpha=(), intensity=())


def test_binary_image_rejects_length_mismatch() -> None:
    with pytest.raises(ValidationFailure, match="alpha length must match dimensions"):
        _ = BinaryImage(width=2, height=2, alpha=(255,), intensity=(255, 255, 255, 255))


def test_detect_content_bounds_encloses_separated_regions_when_disconnected() -> None:
    image = BinaryImage(
        width=6,
        height=4,
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
            255,
            0,
            0,
            255,
            255,
            0,
            255,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
        intensity=(
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            20,
            20,
            255,
            30,
            255,
            255,
            20,
            20,
            255,
            30,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
        ),
    )

    bounds = detect_content_bounds(image=image, background_intensity=255, tolerance=5)

    assert bounds == (1, 1, 5, 3)


def test_detect_separated_region_candidates_splits_disconnected_regions() -> None:
    image = BinaryImage(
        width=6,
        height=4,
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
            255,
            0,
            0,
            255,
            255,
            0,
            255,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
        intensity=(
            255,
            255,
            255,
            255,
            255,
            255,
            255,
            20,
            20,
            255,
            30,
            255,
            255,
            20,
            20,
            255,
            30,
            255,
            255,
            255,
            255,
            255,
            255,
            255,
        ),
    )

    candidates = detect_separated_region_candidates(
        image=image,
        background_intensity=255,
        tolerance=5,
    )

    assert candidates == (
        DetectionCandidate(crop_box=(1, 1, 3, 3), source="deterministic"),
        DetectionCandidate(crop_box=(4, 1, 5, 3), source="deterministic"),
    )


def test_model_candidate_can_compete_with_rule_candidate() -> None:
    service = FakeExtractionService(
        result=ExtractionResult(crop_box=(2, 3, 8, 9), fallback_reason=None),
    )

    candidate = model_candidate_from_extraction(service=service, image_bytes=b"png-bytes")

    assert candidate is not None
    assert candidate.crop_box == (2, 3, 8, 9)
    assert candidate.source == "model"
