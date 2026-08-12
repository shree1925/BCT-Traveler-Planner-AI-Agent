"""The agent loop.

This is what LangChain's AgentExecutor does, written out. Roughly 60 lines
of actual logic: call the model, execute any tools it asked for, feed the
results back, repeat until it stops asking or the step budget runs out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import config
from agent.prompts import build_system_prompt
from agent.registry import TOOL_SCHEMAS, TOOLS
from providers.base import Provider, ProviderError, assistant_msg, system_msg, tool_msg, user_msg
from utils import store
from utils.helpers import truncate
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class TraceStep:
    step: int
    tool: str
    args: dict
    result: str
    ok: bool = True


@dataclass
class AgentResult:
    text: str
    trace: list[TraceStep] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    error: str | None = None


def _execute(name: str, args: dict) -> tuple[str, bool]:
    entry = TOOLS.get(name)
    if entry is None:
        return (
            f"Unknown tool '{name}'. Available tools: {', '.join(TOOLS)}.",
            False,
        )
    _, func = entry
    try:
        result = func(**(args or {}))
        return (str(result), True)
    except TypeError as exc:
        return (f"Tool '{name}' rejected those arguments ({exc}). Check the schema and retry.", False)
    except Exception as exc:  
        log.exception("Tool %s raised", name)
        return (f"Tool '{name}' failed: {exc}", False)


def run_agent(
    user_message: str,
    history: list[dict] | None = None,
    provider: Provider | None = None,
    max_steps: int = config.MAX_AGENT_STEPS,
    on_tool: Callable[[str], None] | None = None,
) -> AgentResult:
    """One user turn, possibly spanning several tool calls.

    `history` is the neutral message list from previous turns (no system turn).
    `on_tool` is called with each tool name before it runs, for UI spinners.
    """
    if provider is None:
        raise ValueError("run_agent requires a provider")

    messages: list[dict] = [system_msg(build_system_prompt())]
    messages.extend(history or [])
    messages.append(user_msg(user_message))

    trace: list[TraceStep] = []
    reasoning: list[str] = []

    for step in range(1, max_steps + 1):
        try:
            reply = provider.chat(messages, TOOL_SCHEMAS)
        except ProviderError as exc:
            return AgentResult(text=str(exc), trace=trace, messages=messages, error=str(exc))
        except Exception as exc:  # pragma: no cover
            log.exception("Provider call failed")
            return AgentResult(
                text=f"The model call failed: {exc}", trace=trace, messages=messages, error=str(exc)
            )

        if reply.reasoning:
            reasoning.append(reply.reasoning)

        if not reply.wants_tools:
            answer = (reply.text or "").strip() or "I could not produce a response. Try rephrasing."
            messages.append(assistant_msg(answer))
            store.put("last_answer", answer)
            return AgentResult(text=answer, trace=trace, messages=messages, reasoning=reasoning)

        messages.append(assistant_msg(reply.text, reply.tool_calls, native=reply.native))

        for call in reply.tool_calls:
            if on_tool:
                try:
                    on_tool(call.name)
                except Exception:
                    pass
            result, ok = _execute(call.name, call.args)
            trace.append(
                TraceStep(step=step, tool=call.name, args=call.args, result=truncate(result, 1200), ok=ok)
            )
            messages.append(tool_msg(call, result))

    fallback = (
        "I used all my available research steps without finishing. Try narrowing the request - "
        "for example, name one city and a trip length."
    )
    messages.append(assistant_msg(fallback))
    return AgentResult(text=fallback, trace=trace, messages=messages, reasoning=reasoning)


def strip_system(messages: list[dict]) -> list[dict]:
    """History to carry into the next turn - the system prompt is rebuilt each time."""
    return [m for m in messages if m.get("role") != "system"]


def trim_history(messages: list[dict], max_messages: int = 24) -> list[dict]:
    """Keep the tail, but never start on an orphaned tool result."""
    trimmed = messages[-max_messages:]
    while trimmed and trimmed[0].get("role") == "tool":
        trimmed = trimmed[1:]
    return trimmed
