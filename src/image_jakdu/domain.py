from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt
from pydantic import ValidationError as PydanticValidationError
from typing_extensions import override

ModeName = Literal["count_grid", "pixel_size", "auto_detect", "model_assisted"]
MAX_TOLERANCE: Final = 255
DEFAULT_TOLERANCE: Final = 12


@dataclass(frozen=True, slots=True)
class ValidationError(Exception):
    message: str

    @override
    def __str__(self) -> str:
        return self.message


ValidationFailure: TypeAlias = ValidationError


@dataclass(frozen=True, slots=True)
class CountGridSettings:
    columns: int
    rows: int

    def __post_init__(self) -> None:
        _require_positive_integer(self.columns, "columns")
        _require_positive_integer(self.rows, "rows")


@dataclass(frozen=True, slots=True)
class PixelSizeSettings:
    tile_width: int
    tile_height: int

    def __post_init__(self) -> None:
        _require_positive_integer(self.tile_width, "tile_width")
        _require_positive_integer(self.tile_height, "tile_height")


@dataclass(frozen=True, slots=True)
class AutoDetectSettings:
    tolerance: int = DEFAULT_TOLERANCE

    def __post_init__(self) -> None:
        _require_integer(self.tolerance, "tolerance")
        if not 0 <= self.tolerance <= MAX_TOLERANCE:
            message = "tolerance must be between 0 and 255"
            raise ValidationFailure(message)


@dataclass(frozen=True, slots=True)
class IntentJobDraft:
    mode: ModeName
    settings: CountGridSettings | PixelSizeSettings | AutoDetectSettings
    use_model_assist: bool
    auto_trim_margins: bool

    @classmethod
    def from_json(cls, raw: str) -> IntentJobDraft:
        try:
            parsed = _IntentPayload.model_validate_json(raw)
        except PydanticValidationError as exc:
            message = "intent response must match the job schema"
            raise ValidationFailure(message) from exc

        settings = _parse_settings(parsed)
        return cls(
            mode=parsed.mode,
            settings=settings,
            use_model_assist=parsed.use_model_assist,
            auto_trim_margins=parsed.auto_trim_margins,
        )


class _IntentPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True, strict=True)

    mode: ModeName
    columns: StrictInt | None = None
    rows: StrictInt | None = None
    tile_width: StrictInt | None = None
    tile_height: StrictInt | None = None
    tolerance: StrictInt | None = None
    use_model_assist: StrictBool
    auto_trim_margins: StrictBool


def _parse_settings(
    payload: _IntentPayload,
) -> CountGridSettings | PixelSizeSettings | AutoDetectSettings:
    match payload.mode:
        case "count_grid":
            return CountGridSettings(
                columns=_require_present(payload.columns, "columns"),
                rows=_require_present(payload.rows, "rows"),
            )
        case "pixel_size":
            return PixelSizeSettings(
                tile_width=_require_present(payload.tile_width, "tile_width"),
                tile_height=_require_present(payload.tile_height, "tile_height"),
            )
        case "auto_detect":
            return AutoDetectSettings(
                tolerance=_optional_tolerance(payload.tolerance),
            )
        case "model_assisted":
            return AutoDetectSettings(
                tolerance=_optional_tolerance(payload.tolerance),
            )


def _require_present(value: int | None, field_name: str) -> int:
    if value is None:
        message = f"{field_name} is required"
        raise ValidationFailure(message)
    return value


def _optional_tolerance(value: int | None) -> int:
    if value is None:
        return DEFAULT_TOLERANCE
    return value


def _require_positive_integer(value: int, field_name: str) -> None:
    _require_integer(value, field_name)
    if value <= 0:
        message = f"{field_name} must be a positive integer"
        raise ValidationFailure(message)


def _require_integer(value: int, field_name: str) -> None:
    if type(value) is not int:
        message = f"{field_name} must be an integer"
        raise ValidationFailure(message)
