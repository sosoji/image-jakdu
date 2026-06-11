import pytest

from image_jakdu.domain import CountGridSettings, PixelSizeSettings, ValidationFailure
from image_jakdu.splitters import ImageBounds, split_by_count_grid, split_by_pixel_size


def test_count_grid_splits_after_trim_into_expected_tiles() -> None:
    bounds = ImageBounds(left=10, top=20, right=110, bottom=100)
    settings = CountGridSettings(columns=2, rows=2)

    crops = split_by_count_grid(bounds=bounds, settings=settings)

    assert crops == (
        (10, 20, 60, 60),
        (60, 20, 110, 60),
        (10, 60, 60, 100),
        (60, 60, 110, 100),
    )


def test_pixel_size_split_includes_expected_tiles() -> None:
    bounds = ImageBounds(left=0, top=0, right=96, bottom=64)
    settings = PixelSizeSettings(tile_width=32, tile_height=32)

    crops = split_by_pixel_size(bounds=bounds, settings=settings)

    assert crops == (
        (0, 0, 32, 32),
        (32, 0, 64, 32),
        (64, 0, 96, 32),
        (0, 32, 32, 64),
        (32, 32, 64, 64),
        (64, 32, 96, 64),
    )


def test_pixel_size_split_includes_non_empty_edge_tiles() -> None:
    bounds = ImageBounds(left=0, top=0, right=70, bottom=33)
    settings = PixelSizeSettings(tile_width=32, tile_height=32)

    crops = split_by_pixel_size(bounds=bounds, settings=settings)

    assert crops == (
        (0, 0, 32, 32),
        (32, 0, 64, 32),
        (64, 0, 70, 32),
        (0, 32, 32, 33),
        (32, 32, 64, 33),
        (64, 32, 70, 33),
    )


def test_rejects_empty_bounds() -> None:
    with pytest.raises(ValidationFailure):
        _ = ImageBounds(left=10, top=0, right=10, bottom=20)

    with pytest.raises(ValidationFailure):
        _ = ImageBounds(left=0, top=5, right=20, bottom=5)
