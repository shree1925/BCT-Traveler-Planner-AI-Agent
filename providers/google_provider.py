"""Google AI Studio provider - serves BOTH Gemini and Gemma.

They differ only by the model string, so one class covers two of the four
user-facing choices.
"""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

import config
from providers.base import Provider, ProviderError, Reply, ToolCall, split_system
from utils.logger import get_logger

log = get_logger(__name__)


class GoogleProvider(Provider):
    def __init__(self, backend: str, meta: dict, api_key: str, model: str):
        self.key = backend
        self.model = model
        self.label = f"{meta['label']} / {model}"
        self._supports_system = True
        self._supports_temperature = config.model_supports_temperature(model)
        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as exc:  # pragma: no cover
            raise ProviderError(f"Could not initialise the Google client: {exc}") from exc

    @staticmethod
    def _to_native_tools(tools: list[dict] | None):
        if not tools:
            return None
        declarations = [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters") or {"type": "object", "properties": {}},
            }
            for t in tools
        ]
        return [types.Tool(function_declarations=declarations)]

    def _to_contents(self, messages: list[dict]) -> list[types.Content]:
        """Neutral messages -> Gemini `contents`.

        Gemini uses the role "model" where the neutral format says
        "assistant", and tool results are function-response parts rather
        than a separate role.
        """
        contents: list[types.Content] = []
        for msg in messages:
            role = msg.get("role")

            if role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part(text=msg.get("content") or "")])
                )

            elif role == "assistant":
                
                
                
                native = msg.get("native")
                if native is not None:
                    contents.append(native)
                    continue

                parts: list[types.Part] = []
                if msg.get("content"):
                    parts.append(types.Part(text=msg["content"]))
                for call in msg.get("tool_calls") or []:
                    part = types.Part(
                        function_call=types.FunctionCall(name=call.name, args=call.args)
                    )
                    if call.signature is not None:
                        try:
                            part.thought_signature = call.signature
                        except Exception:  # older SDK without the field
                            pass
                    parts.append(part)
                if parts:
                    contents.append(types.Content(role="model", parts=parts))

            elif role == "tool":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=msg.get("name", "tool"),
                                response={"result": msg.get("content", "")},
                            )
                        ],
                    )
                )
        return contents


    @staticmethod
    def _parse(response: Any) -> Reply:
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        native = None

        candidates = getattr(response, "candidates", None) or []
        if candidates:
            content = getattr(candidates[0], "content", None)
            native = content
            for part in (getattr(content, "parts", None) or []):
                if getattr(part, "text", None):
                    text_parts.append(part.text)
                fc = getattr(part, "function_call", None)
                if fc is not None and getattr(fc, "name", None):
                    args = dict(getattr(fc, "args", None) or {})
                    call_id = getattr(fc, "id", None)
                    call = ToolCall(name=fc.name, args=args, **({"id": call_id} if call_id else {}))
                    call.signature = getattr(part, "thought_signature", None)
                    calls.append(call)

        # Fallback for SDK versions that only surface .function_calls
        if not calls:
            for fc in (getattr(response, "function_calls", None) or []):
                calls.append(ToolCall(name=fc.name, args=dict(getattr(fc, "args", None) or {})))

        return Reply(
            text="\n".join(p for p in text_parts if p).strip() or None,
            tool_calls=calls,
            raw=response,
            native=native,
        )


    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        system_text, rest = split_system(messages)
        native_tools = self._to_native_tools(tools)

        def _call(use_system_instruction: bool):
            payload = list(rest)
            sys_arg = None
            if system_text:
                if use_system_instruction:
                    sys_arg = system_text
                else:

            
                    payload = list(rest)
                    for i, m in enumerate(payload):
                        if m.get("role") == "user":
                            payload[i] = dict(m, content=f"{system_text}\n\n---\n\n{m['content']}")
                            break
                    else:
                        payload.insert(0, {"role": "user", "content": system_text})

            cfg_kwargs: dict[str, Any] = {
                "max_output_tokens": config.MAX_OUTPUT_TOKENS,
            }
            
            if self._supports_temperature:
                cfg_kwargs["temperature"] = config.TEMPERATURE
            if sys_arg:
                cfg_kwargs["system_instruction"] = sys_arg
            if native_tools:
                cfg_kwargs["tools"] = native_tools

            return self._client.models.generate_content(
                model=self.model,
                contents=self._to_contents(payload),
                config=types.GenerateContentConfig(**cfg_kwargs),
            )

        try:
            response = _call(self._supports_system)
        except Exception as exc:
            message = str(exc)
            
            if self._supports_system and (
                "system_instruction" in message.lower() or "system instruction" in message.lower()
            ):
                log.warning("%s rejected system_instruction; folding into user turn", self.model)
                self._supports_system = False
                try:
                    response = _call(False)
                except Exception as exc2:
                    raise ProviderError(self._explain(exc2)) from exc2
            else:
                raise ProviderError(self._explain(exc)) from exc

        return self._parse(response)

    def _explain(self, exc: Exception) -> str:
        message = str(exc)
        lowered = message.lower()
        if "api key" in lowered or "permission" in lowered or "401" in lowered:
            return (
                f"{self.label}: the Google API key was rejected. Check GOOGLE_API_KEY "
                f"in your .env file. ({message[:200]})"
            )
        if "not found" in lowered or "404" in lowered:
            return (
                f"{self.label}: the model id '{self.model}' was not found. Update it in "
                f"config.py PROVIDERS. ({message[:200]})"
            )
        if "quota" in lowered or "429" in lowered:
            return f"{self.label}: rate limit or quota exhausted. Wait a moment and retry."
        return f"{self.label} request failed: {message[:300]}"
