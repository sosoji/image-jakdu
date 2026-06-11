from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING, ClassVar, TypedDict

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from pathlib import Path


class SmokeCleanup(TypedDict):
    temp_dir_exists: bool


class SmokeReport(TypedDict):
    status: str
    scenarios: list[str]
    generated_inputs: list[str]
    saved_outputs: list[str]
    cleanup: SmokeCleanup


class SmokeReportModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    status: str
    scenarios: list[str]
    generated_inputs: list[str]
    saved_outputs: list[str]
    cleanup: SmokeCleanup


def test_headless_smoke_qa_writes_evidence_and_cleans_temp(tmp_path: Path) -> None:
    output_dir = tmp_path / "smoke"

    completed = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/run_smoke_qa.py",
            "--headless",
            "--output",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    evidence_path = output_dir / "smoke-report.json"
    evidence = SmokeReportModel.model_validate_json(evidence_path.read_text())
    assert completed.returncode == 0
    assert evidence.status == "PASS"
    assert evidence.cleanup["temp_dir_exists"] is False
    assert {"count_grid", "pixel_size", "batch_collision", "model_fallback", "llm_bypass"} <= set(
        evidence.scenarios,
    )
    assert len(evidence.generated_inputs) >= 2
    assert len(evidence.saved_outputs) >= 4
