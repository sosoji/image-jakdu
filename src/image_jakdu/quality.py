from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from image_jakdu.detection import (
    BinaryImage,
    detect_separated_region_candidates,
    trim_uniform_margin,
)
from image_jakdu.domain import ValidationFailure
from image_jakdu.quality_metrics import area, background_ratio, duplicates_previous

if TYPE_CHECKING:
    from image_jakdu.splitters import CropBox


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    min_area: int
    max_background_ratio: float
    duplicate_overlap_ratio: float

    def __post_init__(self) -> None:
        if self.min_area <= 0:
            message = "min_area must be positive"
            raise ValidationFailure(message)
        if not 0.0 <= self.max_background_ratio <= 1.0:
            message = "max_background_ratio must be between 0 and 1"
            raise ValidationFailure(message)
        if not 0.0 <= self.duplicate_overlap_ratio <= 1.0:
            message = "duplicate_overlap_ratio must be between 0 and 1"
            raise ValidationFailure(message)


@dataclass(frozen=True, slots=True)
class CandidatePass:
    source: str
    crop_boxes: tuple[CropBox, ...]
    background_ratios: tuple[float, ...]
    expected_count: int | None

    def __post_init__(self) -> None:
        if len(self.crop_boxes) != len(self.background_ratios):
            message = "background ratio count must match crop count"
            raise ValidationFailure(message)


class PassMetadata(TypedDict):
    source: str
    score: float
    accepted: bool
    rejection_reasons: tuple[str, ...]


class SelectionMetadata(TypedDict):
    chosen_source: str
    chosen_score: float
    chosen_rejection_reasons: tuple[str, ...]
    candidate_count: int
    all_passes: tuple[PassMetadata, ...]


@dataclass(frozen=True, slots=True)
class GeneratedPassRequest:
    source: str
    width: int
    height: int
    alpha: tuple[int, ...]
    intensity: tuple[int, ...]
    background_intensity: int
    tolerance_variants: tuple[int, ...]
    model_crop_box: CropBox | None
    expected_count: int | None


@dataclass(frozen=True, slots=True)
class ScoredPass:
    source: str
    crop_boxes: tuple[CropBox, ...]
    score: float
    accepted: bool
    rejection_reasons: tuple[str, ...]

    @classmethod
    def from_candidate(cls, *, candidate: CandidatePass, policy: QualityPolicy) -> ScoredPass:
        rejection_reasons = _rejection_reasons(candidate=candidate, policy=policy)
        accepted = len(rejection_reasons) == 0
        score = _score_candidate(candidate=candidate, accepted=accepted)
        return cls(
            source=candidate.source,
            crop_boxes=candidate.crop_boxes,
            score=score,
            accepted=accepted,
            rejection_reasons=rejection_reasons,
        )


@dataclass(frozen=True, slots=True)
class SelectionResult:
    chosen: ScoredPass
    all_passes: tuple[ScoredPass, ...]
    metadata: SelectionMetadata


def select_best_pass(
    *,
    candidates: tuple[CandidatePass, ...],
    policy: QualityPolicy,
) -> SelectionResult:
    if len(candidates) == 0:
        message = "at least one candidate pass is required"
        raise ValidationFailure(message)

    all_passes = tuple(
        ScoredPass.from_candidate(candidate=candidate, policy=policy) for candidate in candidates
    )
    chosen = max(all_passes, key=lambda scored: scored.score)
    metadata: SelectionMetadata = {
        "chosen_source": chosen.source,
        "chosen_score": chosen.score,
        "chosen_rejection_reasons": chosen.rejection_reasons,
        "candidate_count": len(all_passes),
        "all_passes": tuple(_metadata_for_pass(scored_pass) for scored_pass in all_passes),
    }
    return SelectionResult(chosen=chosen, all_passes=all_passes, metadata=metadata)


def generate_candidate_passes(*, request: GeneratedPassRequest) -> tuple[CandidatePass, ...]:
    image = BinaryImage(
        width=request.width,
        height=request.height,
        alpha=request.alpha,
        intensity=request.intensity,
    )
    candidates: list[CandidatePass] = []

    for tolerance in request.tolerance_variants:
        trim_box = trim_uniform_margin(
            image=image,
            background_intensity=request.background_intensity,
            tolerance=tolerance,
        )
        if trim_box is not None:
            candidates.append(
                CandidatePass(
                    source=f"trim:tolerance={tolerance}",
                    crop_boxes=(trim_box,),
                    background_ratios=(
                        background_ratio(
                            image=image,
                            crop_box=trim_box,
                            background_intensity=request.background_intensity,
                            tolerance=tolerance,
                        ),
                    ),
                    expected_count=request.expected_count,
                ),
            )

        region_candidates = detect_separated_region_candidates(
            image=image,
            background_intensity=request.background_intensity,
            tolerance=tolerance,
        )
        if len(region_candidates) > 1:
            region_boxes = tuple(candidate.crop_box for candidate in region_candidates)
            candidates.append(
                CandidatePass(
                    source=f"regions:tolerance={tolerance}",
                    crop_boxes=region_boxes,
                    background_ratios=tuple(
                        background_ratio(
                            image=image,
                            crop_box=crop_box,
                            background_intensity=request.background_intensity,
                            tolerance=tolerance,
                        )
                        for crop_box in region_boxes
                    ),
                    expected_count=request.expected_count,
                ),
            )

    if request.model_crop_box is not None:
        candidates.append(
            CandidatePass(
                source="model",
                crop_boxes=(request.model_crop_box,),
                background_ratios=(
                    background_ratio(
                        image=image,
                        crop_box=request.model_crop_box,
                        background_intensity=request.background_intensity,
                        tolerance=0,
                    ),
                ),
                expected_count=request.expected_count,
            ),
        )

    return tuple(_dedupe_candidates(candidates))


def _rejection_reasons(*, candidate: CandidatePass, policy: QualityPolicy) -> tuple[str, ...]:
    reasons: list[str] = []
    previous_boxes: list[CropBox] = []
    for index, crop_box in enumerate(candidate.crop_boxes):
        can_anchor_duplicate = True
        crop_area = area(crop_box)
        if crop_area == 0:
            reasons.append(f"empty crop at index {index}")
            can_anchor_duplicate = False
        elif crop_area < policy.min_area:
            reasons.append(f"tiny crop at index {index}")
            can_anchor_duplicate = False
        if candidate.background_ratios[index] > policy.max_background_ratio:
            reasons.append(f"background-heavy crop at index {index}")
        if duplicates_previous(crop_box, previous_boxes, policy.duplicate_overlap_ratio):
            reasons.append(f"duplicate crop at index {index}")
        if can_anchor_duplicate:
            previous_boxes.append(crop_box)
    if (
        candidate.expected_count is not None
        and len(candidate.crop_boxes) != candidate.expected_count
    ):
        reasons.append("crop count does not match expected count")
    return tuple(reasons)


def _metadata_for_pass(scored_pass: ScoredPass) -> PassMetadata:
    return {
        "source": scored_pass.source,
        "score": scored_pass.score,
        "accepted": scored_pass.accepted,
        "rejection_reasons": scored_pass.rejection_reasons,
    }


def _dedupe_candidates(candidates: list[CandidatePass]) -> tuple[CandidatePass, ...]:
    seen: set[tuple[str, tuple[CropBox, ...]]] = set()
    deduped: list[CandidatePass] = []
    for candidate in candidates:
        key = (_source_family(candidate.source), candidate.crop_boxes)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return tuple(deduped)


def _source_family(source: str) -> str:
    return source.split(":", maxsplit=1)[0]


def _score_candidate(*, candidate: CandidatePass, accepted: bool) -> float:
    count_score = float(len(candidate.crop_boxes))
    foreground_score = sum(1.0 - ratio for ratio in candidate.background_ratios)
    expected_count_bonus = 1.0 if candidate.expected_count == len(candidate.crop_boxes) else 0.0
    penalty = 1000.0 if not accepted else 0.0
    return count_score + foreground_score + expected_count_bonus - penalty
