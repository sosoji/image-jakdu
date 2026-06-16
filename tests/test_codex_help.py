from pathlib import Path
from typing import final

import pytest

from image_jakdu.codex_help import (
    CodexCliHelpProvider,
    CodexCommandResult,
    CodexHelpRequest,
    CodexHelpUnavailableError,
)


@final
class RecordingRunner:
    def __init__(self, result: CodexCommandResult) -> None:
        self.result: CodexCommandResult = result
        self.commands: list[tuple[tuple[str, ...], Path | None, int]] = []

    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path | None,
        timeout_seconds: int,
    ) -> CodexCommandResult:
        self.commands.append((command, cwd, timeout_seconds))
        return self.result


class LastMessageFileRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[str, ...]] = []

    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path | None,
        timeout_seconds: int,
    ) -> CodexCommandResult:
        _ = cwd
        _ = timeout_seconds
        self.commands.append(command)
        output_path = Path(command[command.index("--output-last-message") + 1])
        _ = output_path.write_text("Final Codex answer.")
        return CodexCommandResult(stdout="progress noise\nFinal Codex answer.", stderr="", code=0)


def test_codex_help_provider_runs_codex_read_only_for_current_workspace(tmp_path: Path) -> None:
    runner = RecordingRunner(result=CodexCommandResult(stdout="Use Count grid.", stderr="", code=0))
    provider = CodexCliHelpProvider(runner=runner, cwd=tmp_path, timeout_seconds=45)

    answer = provider.ask(CodexHelpRequest(instruction="How should I split this image?"))

    assert answer == "Use Count grid."
    command, cwd, timeout_seconds = runner.commands[0]
    assert command[:7] == (
        "codex",
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--cd",
        str(tmp_path),
    )
    assert "--output-last-message" in command
    assert "Image Jakdu" in command[-1]
    assert "Do not split images" in command[-1]
    assert "Python processing pipeline" in command[-1]
    assert "How should I split this image?" in command[-1]
    assert cwd == tmp_path
    assert timeout_seconds == 45


def test_codex_help_provider_reads_last_message_file_instead_of_progress_stdout(
    tmp_path: Path,
) -> None:
    runner = LastMessageFileRunner()
    provider = CodexCliHelpProvider(runner=runner, cwd=tmp_path)

    answer = provider.ask(CodexHelpRequest(instruction="Help me"))

    assert answer == "Final Codex answer."


def test_codex_help_provider_reports_cli_failure(tmp_path: Path) -> None:
    runner = RecordingRunner(
        result=CodexCommandResult(stdout="", stderr="not authenticated", code=1),
    )
    provider = CodexCliHelpProvider(runner=runner, cwd=tmp_path)

    with pytest.raises(CodexHelpUnavailableError, match="not authenticated"):
        _ = provider.ask(CodexHelpRequest(instruction="Help me"))
