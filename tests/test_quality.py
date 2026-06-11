from image_jakdu.quality import (
    CandidatePass,
    GeneratedPassRequest,
    QualityPolicy,
    ScoredPass,
    generate_candidate_passes,
    select_best_pass,
)


def test_rejects_empty_tiny_duplicate_and_background_crops() -> None:
    policy = QualityPolicy(min_area=4, max_background_ratio=0.8, duplicate_overlap_ratio=0.9)
    candidate = CandidatePass(
        source="deterministic",
        crop_boxes=(
            (0, 0, 0, 10),
            (0, 0, 1, 1),
            (0, 0, 10, 10),
            (0, 0, 10, 10),
        ),
        background_ratios=(0.0, 0.0, 0.95, 0.0),
        expected_count=None,
    )

    scored = ScoredPass.from_candidate(candidate=candidate, policy=policy)

    assert scored.accepted is False
    assert scored.rejection_reasons == (
        "empty crop at index 0",
        "tiny crop at index 1",
        "background-heavy crop at index 2",
        "duplicate crop at index 3",
    )


def test_selects_best_candidate_pass_and_records_metadata() -> None:
    policy = QualityPolicy(min_area=4, max_background_ratio=0.8, duplicate_overlap_ratio=0.9)
    weak = CandidatePass(
        source="rule",
        crop_boxes=((0, 0, 10, 10),),
        background_ratios=(0.5,),
        expected_count=2,
    )
    strong = CandidatePass(
        source="model",
        crop_boxes=((0, 0, 10, 10), (12, 0, 22, 10)),
        background_ratios=(0.1, 0.2),
        expected_count=2,
    )

    result = select_best_pass(candidates=(weak, strong), policy=policy)

    assert result.chosen.source == "model"
    assert result.chosen.score > result.all_passes[0].score
    assert result.chosen.rejection_reasons == ()
    assert result.metadata["chosen_source"] == "model"
    assert result.metadata["candidate_count"] == 2
    assert result.metadata["chosen_score"] == result.chosen.score
    assert result.metadata["chosen_rejection_reasons"] == ()
    assert result.metadata["all_passes"][0]["source"] == "rule"
    assert result.metadata["all_passes"][0]["rejection_reasons"] == (
        "crop count does not match expected count",
    )


def test_generates_candidate_passes_from_trim_regions_and_model_masks() -> None:
    request = GeneratedPassRequest(
        source="auto",
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
        background_intensity=255,
        tolerance_variants=(0, 5),
        model_crop_box=(1, 1, 5, 3),
        expected_count=2,
    )

    candidates = generate_candidate_passes(request=request)

    assert candidates == (
        CandidatePass(
            source="trim:tolerance=0",
            crop_boxes=((1, 1, 5, 3),),
            background_ratios=(0.25,),
            expected_count=2,
        ),
        CandidatePass(
            source="regions:tolerance=0",
            crop_boxes=((1, 1, 3, 3), (4, 1, 5, 3)),
            background_ratios=(0.0, 0.0),
            expected_count=2,
        ),
        CandidatePass(
            source="model",
            crop_boxes=((1, 1, 5, 3),),
            background_ratios=(0.25,),
            expected_count=2,
        ),
    )
