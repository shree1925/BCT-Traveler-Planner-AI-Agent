"""OpenAI-compatible provider.

Serves BOTH Nemotron routes - NVIDIA NIM and the Hugging Face router -
because both expose the same `/chat/completions` contract. The only
difference is `base_url` and which key is used.

Uses `requests` directly; the `openai` SDK is not an allowed dependency.
"""

from __future__ import annotations

import json
from typing import Any

import requests

import config
from providers.base import Provider, ProviderError, Reply, ToolCall
from utils.logger import get_logger

log = get_logger(__name__)


class OpenAICompatProvider(Provider):
    def __init__(self, backend: str, meta: dict, api_key: str, model: str):
        self.key = backend
        self.model = model
        self.label = f"{meta['label']} / {model}"
        self.base_url = str(meta["base_url"]).rstrip("/")
        self._api_key = api_key
        self._extra_body = config.model_extra_body(backend, model)

    
    @staticmethod
    def _to_native_tools(tools: list[dict] | None):
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters") or {"type": "object", "properties": {}},
                },
            }
            for t in tools
        ]

    
    @staticmethod
    def _to_native_messages(messages: list[dict]) -> list[dict]:
        out: list[dict] = []
        for msg in messages:
            role = msg.get("role")

            if role in ("system", "user"):
                out.append({"role": role, "content": msg.get("content") or ""})

            elif role == "assistant":
                entry: dict[str, Any] = {"role": "assistant", "content": msg.get("content") or ""}
                calls = msg.get("tool_calls") or []
                if calls:
                    entry["tool_calls"] = [
                        {
                            "id": c.id,
                            "type": "function",
                            "function": {"name": c.name, "arguments": json.dumps(c.args)},
                        }
                        for c in calls
                    ]
                out.append(entry)

            elif role == "tool":
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.get("tool_call_id", ""),
                        "name": msg.get("name", "tool"),
                        "content": msg.get("content") or "",
                    }
                )
        return out

    
    @staticmethod
    def _parse(payload: dict) -> Reply:
        choices = payload.get("choices") or []
        if not choices:
            return Reply(text=None, raw=payload)
        message = choices[0].get("message") or {}

        calls: list[ToolCall] = []
        for raw_call in message.get("tool_calls") or []:
            fn = raw_call.get("function") or {}
            name = fn.get("name")
            if not name:
                continue
            raw_args = fn.get("arguments")
            if isinstance(raw_args, dict):
                args = raw_args
            else:
                try:
                    args = json.loads(raw_args or "{}")
                except (TypeError, ValueError):
                    log.warning("Malformed tool arguments for %s: %r", name, raw_args)
                    args = {}
            if not isinstance(args, dict):
                args = {}
            calls.append(ToolCall(name=name, args=args, id=raw_call.get("id") or ToolCall(name, {}).id))

        
        reasoning = message.get("reasoning_content") or message.get("reasoning")

        return Reply(
            text=(message.get("content") or None),
            tool_calls=calls,
            reasoning=reasoning,
            raw=payload,
        )

    
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> Reply:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": self._to_native_messages(messages),
            "temperature": config.TEMPERATURE,
            "max_tokens": config.MAX_OUTPUT_TOKENS,
            "stream": False,
        }
        if self._extra_body:
            body.update(self._extra_body)

        native_tools = self._to_native_tools(tools)
        if native_tools:
            body["tools"] = native_tools
            body["tool_choice"] = "auto"

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=config.LLM_TIMEOUT)
        except requests.Timeout as exc:
            raise ProviderError(
                f"{self.label} timed out after {config.LLM_TIMEOUT}s. Reasoning models can be "
                f"slow - try a smaller model id in config.py."
            ) from exc
        except requests.RequestException as exc:
            raise ProviderError(f"{self.label}: network error - {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise ProviderError(
                f"{self.label}: key rejected ({response.status_code}). Check the env var for "
                f"this provider in your .env file."
            )
        if response.status_code == 404:
            raise ProviderError(
                f"{self.label}: model id '{self.model}' not found at {self.base_url}. "
                f"Update PROVIDERS in config.py."
            )
        if response.status_code == 429:
            raise ProviderError(
                f"{self.label}: rate limited. The free tier allows roughly 40 requests/minute - "
                f"wait a few seconds and retry."
            )
        if response.status_code >= 400:
            body = response.text or ""
            
            
            if "model_not_supported" in body or "not supported by any provider" in body:
                raise ProviderError(
                    f"{self.label}: '{self.model}' exists, but none of the inference "
                    f"providers enabled on your account serves it. Enable more providers at "
                    f"https://hf.co/settings/inference-providers, check which provider lists "
                    f"the model on its Hugging Face page, or pin one by appending a suffix to "
                    f"the model id in config.py (e.g. '{self.model}:together')."
                )
            if "model_not_found" in body or "does not exist" in body:
                raise ProviderError(
                    f"{self.label}: model id '{self.model}' does not exist at {self.base_url}. "
                    f"Copy the exact repo id from the model page and update PROVIDERS in "
                    f"config.py. On Hugging Face the id often ends in a precision suffix "
                    f"such as -BF16."
                )
            raise ProviderError(
                f"{self.label} returned HTTP {response.status_code}: {body[:300]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError(f"{self.label} returned non-JSON: {response.text[:200]}") from exc

        if "error" in payload and not payload.get("choices"):
            raise ProviderError(f"{self.label}: {str(payload['error'])[:300]}")

        return self._parse(payload)
