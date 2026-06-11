from __future__ import annotations

from pathlib import Path, PureWindowsPath

PathInput = Path | PureWindowsPath


class OutputWriteError(RuntimeError):
    pass


def ensure_output_accessible(output_root: PathInput) -> None:
    folder = Path(output_root)
    folder.mkdir(parents=True, exist_ok=True)
    mode = folder.stat().st_mode
    if mode & 0o222 == 0:
        message = "Cannot write to output folder"
        raise OutputWriteError(message)


def reserve_output_paths(*, output_paths: tuple[Path, ...]) -> None:
    for output_path in output_paths:
        if output_path.exists():
            message = f"Output file already exists and will not be overwritten: {output_path}"
            raise OutputWriteError(message)


def write_output(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as output_file:
            _ = output_file.write(content)
    except FileExistsError as exc:
        message = f"Output file already exists and will not be overwritten: {path}"
        raise OutputWriteError(message) from exc


def write_metadata_file(*, output_root: PathInput, lines: tuple[str, ...]) -> Path:
    folder = Path(output_root)
    metadata_path = folder / "image-jakdu-metadata.txt"
    try:
        with metadata_path.open("x", encoding="utf-8") as metadata_file:
            _ = metadata_file.write("\n".join(lines) + "\n")
    except FileExistsError as exc:
        message = f"Metadata file already exists and will not be overwritten: {metadata_path}"
        raise OutputWriteError(message) from exc
    return metadata_path
