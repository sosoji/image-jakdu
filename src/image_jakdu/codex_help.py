from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from typing_extensions import override


@dataclass(frozen=True, slots=True)
class CodexHelpRequest:
    instruction: str


@dataclass(frozen=True, slots=True)
class CodexCommandResult:
    stdout: str
    stderr: str
    code: int


class CodexCommandRunner(Protocol):
    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path | None,
        timeout_seconds: int,
    ) -> CodexCommandResult: ...


CodexHelpProvider = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class CodexHelpUnavailableError(Exception):
    reason: str

    @override
    def __str__(self) -> str:
        return f"codex help unavailable: {self.reason}"


@dataclass(frozen=True, slots=True)
class SubprocessCodexRunner:
    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path | None,
        timeout_seconds: int,
    ) -> CodexCommandResult:
        try:
            completed = subprocess.run(  # noqa: S603
                command,
                cwd=cwd,
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise CodexHelpUnavailableError(reason="codex executable was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise CodexHelpUnavailableError(reason="codex help timed out") from exc
        return CodexCommandResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            code=completed.returncode,
        )


@dataclass(frozen=True, slots=True)
class CodexCliHelpProvider:
    runner: CodexCommandRunner = SubprocessCodexRunner()
    cwd: Path | None = None
    timeout_seconds: int = 120
    executable: str = "codex"

    def ask(self, request: CodexHelpRequest) -> str:
        workspace = self.cwd or Path.cwd()
        with tempfile.TemporaryDirectory(prefix="image-jakdu-codex-") as temp_dir:
            output_path = Path(temp_dir) / "last-message.txt"
            result = self.runner.run(
                (
                    self.executable,
                    "exec",
                    "--ephemeral",
                    "--sandbox",
                    "read-only",
                    "--cd",
                    str(workspace),
                    "--output-last-message",
                    str(output_path),
                    _build_prompt(request.instruction),
                ),
                cwd=workspace,
                timeout_seconds=self.timeout_seconds,
            )
            answer = _read_answer(output_path=output_path, result=result)
        if result.code != 0:
            raise CodexHelpUnavailableError(reason=_failure_reason(result))
        if answer == "":
            raise CodexHelpUnavailableError(reason="codex returned an empty answer")
        return answer


def default_codex_help_provider(instruction: str) -> str:
    return CodexCliHelpProvider().ask(CodexHelpRequest(instruction=instruction))


def _failure_reason(result: CodexCommandResult) -> str:
    stderr = result.stderr.strip()
    if stderr != "":
        return stderr
    stdout = result.stdout.strip()
    if stdout != "":
        return stdout
    return f"codex exited with status {result.code}"


def _read_answer(*, output_path: Path, result: CodexCommandResult) -> str:
    if output_path.exists():
        answer = output_path.read_text().strip()
        if answer != "":
            return answer
    return result.stdout.strip()


def _build_prompt(instruction: str) -> str:
    return (
        "You are helping a user operate Image Jakdu, a local image-splitting GUI. "
        "Give concise practical guidance only. Do not edit files, run commands, "
        "or request secrets. Do not split images; Image Jakdu's Python processing "
        "pipeline performs the actual image splitting after the user presses Process. "
        "If the request is about choosing split settings, "
        "recommend a mode and concrete values when possible. "
        f"User request: {instruction}"
    )
