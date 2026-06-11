from __future__ import annotations

from pathlib import Path, PureWindowsPath

import pytest
from PIL import Image

from image_jakdu.domain import CountGridSettings, ModeName, PixelSizeSettings
from image_jakdu.gui.job import GuiProcessRequest
from image_jakdu.processor import save_batch_workflow


def make_request(
    sources: list[PureWindowsPath],
    output: PureWindowsPath,
    *,
    mode: ModeName = "count_grid",
    include_metadata: bool = False,
) -> GuiProcessRequest:
    if mode == "count_grid":
        settings: CountGridSettings | PixelSizeSettings = CountGridSettings(columns=1, rows=1)
    elif mode == "pixel_size":
        settings = PixelSizeSettings(tile_width=16, tile_height=16)
    else:
        settings = CountGridSettings(columns=1, rows=1)
    return GuiProcessRequest(
        sources=tuple(sources),
        output_folder=output,
        mode=mode,
        settings=settings,
        use_model_assist=False,
        auto_trim_margins=False,
        write_metadata=include_metadata,
    )


def report_progress(_processed: int, _total: int, _message: str) -> None:
    return


def is_not_cancelled() -> bool:
    return False


def test_batch_outputs_are_saved_with_original_name_plus_number(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    src1 = PureWindowsPath(r"C:\images\foo.png")
    src2 = PureWindowsPath(r"C:\images\bar.png")
    req = make_request([src1, src2], PureWindowsPath(str(out_dir)))

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert len(saved) == 2
    assert saved[0].name == "foo1.png"
    assert saved[1].name == "bar1.png"
    assert (out_dir / "foo1.png").exists()
    assert (out_dir / "bar1.png").exists()


def test_same_basename_inputs_use_source_subfolders(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    src1 = PureWindowsPath(r"C:\images\a\foo.png")
    src2 = PureWindowsPath(r"C:\images\b\foo.png")
    req = make_request([src1, src2], PureWindowsPath(str(out_dir)))

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert len(saved) == 2
    assert saved[0].name == "foo1.png"
    assert saved[1].name == "foo1.png"
    assert saved[0] == PureWindowsPath(str(out_dir)) / "foo" / "foo1.png"
    assert saved[1] == PureWindowsPath(str(out_dir)) / "foo_2" / "foo1.png"
    assert (out_dir / "foo" / "foo1.png").exists()
    assert (out_dir / "foo_2" / "foo1.png").exists()


def test_unwritable_output_folder_reports_error_without_partial_claim(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_dir.chmod(0o444)
    src1 = PureWindowsPath(r"C:\images\foo.png")
    req = make_request([src1], PureWindowsPath(str(out_dir)))

    with pytest.raises(RuntimeError, match="Cannot write to output folder"):
        _ = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert list(out_dir.iterdir()) == []
    out_dir.chmod(0o777)


def test_count_grid_mode_respects_tile_counts(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    src1 = PureWindowsPath(r"C:\images\big.png")
    req = GuiProcessRequest(
        sources=(src1,),
        output_folder=PureWindowsPath(str(out_dir)),
        mode="count_grid",
        settings=CountGridSettings(columns=2, rows=2),
        use_model_assist=False,
        auto_trim_margins=False,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert len(saved) == 4
    assert saved == (
        PureWindowsPath(str(out_dir)) / "big1.png",
        PureWindowsPath(str(out_dir)) / "big2.png",
        PureWindowsPath(str(out_dir)) / "big3.png",
        PureWindowsPath(str(out_dir)) / "big4.png",
    )


def test_existing_image_source_is_saved_as_real_cropped_images(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    source = tmp_path / "source.png"
    image = Image.new("RGB", (8, 4), "red")
    image.paste("blue", (4, 0, 8, 4))
    image.save(source)
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(out_dir),
        mode="count_grid",
        settings=CountGridSettings(columns=2, rows=1),
        use_model_assist=False,
        auto_trim_margins=False,
        write_metadata=False,
    )

    saved = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert len(saved) == 2
    with Image.open(Path(saved[0])) as first:
        assert first.size == (4, 4)
        assert first.getpixel((0, 0)) == (255, 0, 0)
    with Image.open(Path(saved[1])) as second:
        assert second.size == (4, 4)
        assert second.getpixel((0, 0)) == (0, 0, 255)


def test_existing_outputs_are_not_overwritten(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    src1 = PureWindowsPath(r"C:\images\foo.png")
    _ = (out_dir / "foo1.png").write_text("existing")
    req = make_request([src1], PureWindowsPath(str(out_dir)))

    with pytest.raises(RuntimeError, match="already exists"):
        _ = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert (out_dir / "foo1.png").read_text() == "existing"


def test_existing_real_image_output_is_not_overwritten(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    source = tmp_path / "foo.png"
    Image.new("RGB", (4, 4), "red").save(source)
    existing = out_dir / "foo1.png"
    Image.new("RGB", (4, 4), "blue").save(existing)
    req = GuiProcessRequest(
        sources=(PureWindowsPath(source),),
        output_folder=PureWindowsPath(out_dir),
        mode="count_grid",
        settings=CountGridSettings(columns=1, rows=1),
        use_model_assist=False,
        auto_trim_margins=False,
        write_metadata=False,
    )

    with pytest.raises(RuntimeError, match="already exists"):
        _ = save_batch_workflow(req, report_progress, is_not_cancelled)

    with Image.open(existing) as image:
        assert image.getpixel((0, 0)) == (0, 0, 255)


def test_existing_metadata_file_is_not_overwritten(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    metadata = out_dir / "image-jakdu-metadata.txt"
    _ = metadata.write_text("existing\n")
    src1 = PureWindowsPath(r"C:\images\foo.png")
    req = make_request([src1], PureWindowsPath(str(out_dir)), include_metadata=True)

    with pytest.raises(RuntimeError, match="Metadata file already exists"):
        _ = save_batch_workflow(req, report_progress, is_not_cancelled)

    assert metadata.read_text() == "existing\n"


def test_metadata_written_when_requested(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    src1 = PureWindowsPath(r"C:\images\foo.png")
    req = make_request([src1], PureWindowsPath(str(out_dir)), include_metadata=True)

    _ = save_batch_workflow(req, report_progress, is_not_cancelled)

    metadata = out_dir / "image-jakdu-metadata.txt"
    assert metadata.exists()
    raw = metadata.read_text()
    assert "mode=count_grid" in raw
    assert "outputs=1" in raw
    assert "foo1.png" in raw
