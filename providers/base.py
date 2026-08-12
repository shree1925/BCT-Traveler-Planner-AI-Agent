"""Neutral provider interface.

The agent loop only ever sees the types in this file. Every provider
translates the neutral message list into its own wire format on the way out
and normalises the response back into `Reply` on the way in.

Neutral message shapes
----------------------
    {"role": "system",    "content": str}
    {"role": "user",      "content": str}
    {"role": "assistant", "content": str | None, "tool_calls": [ToolCall, ...]}
    {"role": "tool",      "content": str, "tool_call_id": str, "name": str}
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    args: dict
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    signature: Any = None


@dataclass
class Reply:
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    reasoning: str | None = None
    raw: Any = None
    native: Any = None

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


class ProviderError(RuntimeError):
    """Raised for anything the user can act on: bad key, bad model, timeout."""


class Provider(ABC):
    key: str
    label: str
    model: str

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        """Single turn. `tools` is a list of neutral JSON-Schema tool dicts:

            {"name": ..., "description": ..., "parameters": {JSON Schema}}
        """

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} model={self.model!r}>"


def system_msg(content: str) -> dict:
    return {"role": "system", "content": content}


def user_msg(content: str) -> dict:
    return {"role": "user", "content": content}


def assistant_msg(
    content: str | None,
    tool_calls: list[ToolCall] | None = None,
    native: Any = None,
) -> dict:
    return {
        "role": "assistant",
        "content": content,
        "tool_calls": tool_calls or [],
        "native": native,
    }


def tool_msg(call: ToolCall, content: str) -> dict:
    return {
        "role": "tool",
        "content": content,
        "tool_call_id": call.id,
        "name": call.name,
    }


def split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """Pull system turns out of the list and join them."""
    system_parts = [m["content"] for m in messages if m.get("role") == "system" and m.get("content")]
    rest = [m for m in messages if m.get("role") != "system"]
    return "\n\n".join(system_parts), rest
