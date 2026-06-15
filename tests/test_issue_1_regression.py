from __future__ import annotations

from pathlib import Path, PureWindowsPath

from PIL import Image

from image_jakdu.domain import AutoDetectSettings, CountGridSettings, PixelSizeSettings
from image_jakdu.gui.job import GuiProcessRequest
from image_jakdu.processor import save_batch_workflow


def report_progress(_processed: int, _total: int, _message: str) -> None:
    return


def is_not_cancelled() -> bool:
    return False


def test_auto_trim_black_margin_before_count_grid_split(tmp_path: Path) -> None:
    source = _make_black_margin_image(tmp_path / "black-margin.png")
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(tmp_path / "out"),
        mode="count_grid",
        settings=CountGridSettings(columns=2, rows=1),
        use_model_assist=False,
        auto_trim_margins=True,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    _assert_two_color_tiles(saved)


def test_tiff_source_outputs_are_encoded_as_tiff(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    Image.new("RGB", (4, 4), "green").save(source)
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(tmp_path / "out"),
        mode="count_grid",
        settings=CountGridSettings(columns=1, rows=1),
        use_model_assist=False,
        auto_trim_margins=False,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert saved[0].suffix == ".tif"
    with Image.open(Path(saved[0])) as output:
        assert output.format == "TIFF"


def test_tiff_extension_outputs_are_encoded_as_tiff(tmp_path: Path) -> None:
    source = tmp_path / "source.tiff"
    Image.new("RGB", (4, 4), "green").save(source)
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(tmp_path / "out"),
        mode="count_grid",
        settings=CountGridSettings(columns=1, rows=1),
        use_model_assist=False,
        auto_trim_margins=False,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert saved[0].suffix == ".tiff"
    with Image.open(Path(saved[0])) as output:
        assert output.format == "TIFF"


def test_pixel_size_auto_trim_plans_outputs_from_trimmed_bounds(tmp_path: Path) -> None:
    source = _make_black_margin_image(tmp_path / "black-margin.png")
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(tmp_path / "out"),
        mode="pixel_size",
        settings=PixelSizeSettings(tile_width=2, tile_height=2),
        use_model_assist=False,
        auto_trim_margins=True,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert sorted(path.name for path in saved) == ["black-margin1.png", "black-margin2.png"]
    _assert_two_color_tiles(saved)


def test_model_assisted_mode_falls_back_without_processing_failure(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (6, 4), "purple").save(source)
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(tmp_path / "out"),
        mode="model_assisted",
        settings=AutoDetectSettings(),
        use_model_assist=True,
        auto_trim_margins=False,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert len(saved) == 1
    with Image.open(Path(saved[0])) as output:
        assert output.size == (6, 4)


def _make_black_margin_image(path: Path) -> Path:
    image = Image.new("RGB", (8, 4), "black")
    image.paste("red", (2, 1, 4, 3))
    image.paste("blue", (4, 1, 6, 3))
    image.save(path)
    return path


def _assert_two_color_tiles(saved: tuple[PureWindowsPath, ...]) -> None:
    assert len(saved) == 2
    with Image.open(Path(saved[0])) as first:
        assert first.size == (2, 2)
        assert first.getpixel((0, 0)) == (255, 0, 0)
    with Image.open(Path(saved[1])) as second:
        assert second.size == (2, 2)
        assert second.getpixel((0, 0)) == (0, 0, 255)
