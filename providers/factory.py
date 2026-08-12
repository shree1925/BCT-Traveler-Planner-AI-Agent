"""Provider factory - maps a backend + model id to a concrete Provider."""

from __future__ import annotations

import config
from providers.base import Provider, ProviderError
from utils.logger import get_logger

log = get_logger(__name__)


def get_provider(backend: str, model: str | None = None) -> Provider:
    meta = config.BACKENDS.get(backend)
    if meta is None:
        raise ProviderError(
            f"Unknown backend '{backend}'. Valid options: {', '.join(config.BACKENDS)}"
        )

    model = (model or meta["default_model"]).strip()
    if not model:
        raise ProviderError(f"No model selected for {meta['label']}.")

    api_key = config.get_secret(meta["env"])
    if not api_key:
        raise ProviderError(
            f"{meta['label']} needs {meta['env']}, which is not set. "
            f"Add it in the sidebar or your .env file - free key at {meta['key_url']}."
        )

    try:
        if meta["transport"] == "google":
            from providers.google_provider import GoogleProvider

            return GoogleProvider(backend, meta, api_key, model)

        if meta["transport"] == "openai":
            from providers.openai_compat_provider import OpenAICompatProvider

            return OpenAICompatProvider(backend, meta, api_key, model)
    except ImportError as exc:
        raise ProviderError(
            f"{meta['label']} needs a package that is not installed ({exc}). "
            f"Run: pip install -r requirements.txt"
        ) from exc

    raise ProviderError(f"Unsupported transport '{meta['transport']}' for backend '{backend}'.")


def smoke_test(backend: str, model: str | None = None) -> str:
    """Round-trip one message. Used by the sidebar 'Test connection' button."""
    provider = get_provider(backend, model)
    reply = provider.chat(
        [
            {"role": "system", "content": "Reply with exactly one short sentence."},
            {"role": "user", "content": "Say hello and name the model you are."},
        ]
    )
    return (reply.text or "(empty response)").strip()
