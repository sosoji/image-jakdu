from pathlib import PureWindowsPath

from image_jakdu.paths import (
    OutputPlanInput,
    build_output_plan,
    normalize_windows_path,
)


def test_windows_paths_preserve_drive_unicode_and_spaces() -> None:
    raw_path = r"C:\Users\Test User\이미지 작두\out"

    normalized = normalize_windows_path(raw_path)

    assert normalized == PureWindowsPath(raw_path)
    assert normalized.drive == "C:"
    assert "Test User" in normalized.parts
    assert "이미지 작두" in normalized.parts


def test_same_basename_uses_subfolders_but_plain_numbered_files() -> None:
    output_root = PureWindowsPath(r"C:\Users\Test User\결과")
    first = OutputPlanInput(
        source_path=PureWindowsPath(r"C:\input-a\photo.png"),
        tile_count=2,
    )
    second = OutputPlanInput(
        source_path=PureWindowsPath(r"D:\input-b\photo.png"),
        tile_count=2,
    )

    plan = build_output_plan(output_root=output_root, inputs=(first, second))

    assert plan[0].files == (
        PureWindowsPath(r"C:\Users\Test User\결과\photo\photo1.png"),
        PureWindowsPath(r"C:\Users\Test User\결과\photo\photo2.png"),
    )
    assert plan[1].files == (
        PureWindowsPath(r"C:\Users\Test User\결과\photo_2\photo1.png"),
        PureWindowsPath(r"C:\Users\Test User\결과\photo_2\photo2.png"),
    )
