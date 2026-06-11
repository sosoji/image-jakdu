from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import ClassVar, Protocol

import httpx2
from pydantic import BaseModel, ConfigDict
from pydantic import ValidationError as PydanticValidationError
from typing_extensions import override

from image_jakdu.domain import IntentJobDraft, ValidationFailure

_LIMITS = httpx2.Limits(
    max_connections=200,
    max_keepalive_connections=40,
    keepalive_expiry=30.0,
)
_TIMEOUT = httpx2.Timeout(
    connect=5.0,
    read=30.0,
    write=10.0,
    pool=10.0,
)
_SOCKET_OPTIONS: list[tuple[int, int, int]] = [
    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
]


class IntentTransport(Protocol):
    def complete(self, instruction: str) -> str: ...


@dataclass(frozen=True, slots=True)
class IntentServiceUnavailableError(Exception):
    endpoint: str

    @override
    def __str__(self) -> str:
        return f"intent service unavailable: {self.endpoint}"


@dataclass(frozen=True, slots=True)
class IntentClarifier:
    transport: IntentTransport

    def clarify(self, instruction: str) -> IntentJobDraft:
        return IntentJobDraft.from_json(self.transport.complete(instruction))


@dataclass(frozen=True, slots=True)
class ManualIntentFallback:
    clarifier: IntentClarifier
    manual_draft: IntentJobDraft

    def clarify_or_manual(self, instruction: str) -> IntentJobDraft:
        try:
            return self.clarifier.clarify(instruction)
        except IntentServiceUnavailableError:
            return self.manual_draft


@dataclass(frozen=True, slots=True)
class OllamaIntentTransport:
    endpoint: str = "http://localhost:11434"
    model: str = "qwen2.5:1.5b-instruct"

    def complete(self, instruction: str) -> str:
        payload = {
            "model": self.model,
            "prompt": _build_prompt(instruction),
            "stream": False,
            "format": "json",
        }
        try:
            with _create_client(base_url=self.endpoint) as client:
                response = client.post("/api/generate", json=payload)
                _ = response.raise_for_status()
        except httpx2.HTTPError as exc:
            raise IntentServiceUnavailableError(endpoint=self.endpoint) from exc

        try:
            body = _OllamaGenerateResponse.model_validate_json(response.text)
        except PydanticValidationError as exc:
            message = "ollama response did not match expected schema"
            raise ValidationFailure(message) from exc
        if body.response == "":
            raise IntentServiceUnavailableError(endpoint=self.endpoint)
        return body.response


class _OllamaGenerateResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

    response: str


def _create_client(base_url: str) -> httpx2.Client:
    transport = httpx2.HTTPTransport(
        http2=True,
        retries=3,
        limits=_LIMITS,
        socket_options=_SOCKET_OPTIONS,
    )
    return httpx2.Client(
        transport=transport,
        timeout=_TIMEOUT,
        base_url=base_url,
        headers={},
        follow_redirects=True,
    )


def _build_prompt(instruction: str) -> str:
    return (
        "Return only JSON for Image Jakdu settings. "
        "Allowed modes: count_grid, pixel_size, auto_detect, model_assisted. "
        "Required booleans: use_model_assist, auto_trim_margins. "
        "Never include cloud or filesystem actions. "
        f"User instruction: {instruction}"
    )
