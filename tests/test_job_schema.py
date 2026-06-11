import json

import pytest

from image_jakdu.domain import (
    CountGridSettings,
    IntentJobDraft,
    PixelSizeSettings,
    ValidationFailure,
)


def test_rejects_invalid_counts_and_pixels() -> None:
    with pytest.raises(ValidationFailure):
        _ = CountGridSettings(columns=0, rows=2)

    with pytest.raises(ValidationFailure):
        _ = CountGridSettings(columns=2, rows=-1)

    with pytest.raises(ValidationFailure):
        _ = PixelSizeSettings(tile_width=32, tile_height=0)

    with pytest.raises(ValidationFailure):
        _ = IntentJobDraft.from_json(
            json.dumps(
                {
                    "mode": "count_grid",
                    "columns": 1.5,
                    "rows": 2,
                    "use_model_assist": False,
                    "auto_trim_margins": True,
                },
            ),
        )

    with pytest.raises(ValidationFailure):
        _ = IntentJobDraft.from_json(
            json.dumps(
                {
                    "mode": "pixel_size",
                    "tile_width": "64",
                    "tile_height": 48,
                    "use_model_assist": False,
                    "auto_trim_margins": True,
                },
            ),
        )

    valid_count = CountGridSettings(columns=3, rows=2)
    valid_pixel = PixelSizeSettings(tile_width=64, tile_height=48)

    assert valid_count.columns == 3
    assert valid_count.rows == 2
    assert valid_pixel.tile_width == 64
    assert valid_pixel.tile_height == 48


def test_parses_llm_structured_json_job() -> None:
    raw = (
        '{"mode":"count_grid","columns":4,"rows":3,'
        '"use_model_assist":true,"auto_trim_margins":true}'
    )

    draft = IntentJobDraft.from_json(raw)

    assert draft.mode == "count_grid"
    assert isinstance(draft.settings, CountGridSettings)
    assert draft.settings.columns == 4
    assert draft.settings.rows == 3
    assert draft.use_model_assist is True
    assert draft.auto_trim_margins is True


def test_rejects_free_form_llm_text() -> None:
    with pytest.raises(ValidationFailure):
        _ = IntentJobDraft.from_json("가로 4개 세로 3개로 잘라줘")
