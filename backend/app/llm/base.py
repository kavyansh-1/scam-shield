import asyncio
import json
import logging
import re
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from ..config import settings

log = logging.getLogger("scamshield.llm")
T = TypeVar("T", bound=BaseModel)
Image = tuple  # (bytes, mime)


class BaseLLM:
    name = "base"

    async def raw(self, system: str, user: str, image: Optional[Image], timeout: float) -> str:
        raise NotImplementedError

    async def complete_json(self, system: str, user: str, schema: Type[T], image: Optional[Image] = None,
                            timeout: float = 12, hint: Optional[dict] = None) -> T:
        sys2 = system + "\n\nRespond with ONLY one JSON object (no markdown fences, no commentary) matching this JSON schema:\n" + json.dumps(schema.model_json_schema())
        last: Exception | None = None
        for attempt in range(2):
            u = user if attempt == 0 else user + "\n\nYour previous answer was not valid JSON for the schema. Return ONLY the JSON object."
            try:
                text = await asyncio.wait_for(self.raw(sys2, u, image, timeout), timeout + 2)
                return schema.model_validate(json.loads(_extract_json(text)))
            except (ValidationError, ValueError) as e:  # bad JSON -> one retry
                last = e
                log.warning("LLM invalid JSON (attempt %s): %s", attempt + 1, e)
        raise ValueError(f"LLM returned invalid JSON: {last}")


def _extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    a, b = text.find("{"), text.rfind("}")
    return text[a:b + 1] if a != -1 and b > a else text


_client: BaseLLM | None = None


def get_client() -> BaseLLM:
    """Provider from settings; any misconfiguration silently falls back to the mock client."""
    global _client
    if _client is not None:
        return _client
    provider = settings.LLM_PROVIDER.lower().strip()
    try:
        if provider != "mock":
            if not settings.LLM_MODEL:
                raise RuntimeError("LLM_MODEL is empty")
            if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
                from .anthropic_client import AnthropicClient
                _client = AnthropicClient()
            elif provider == "gemini" and settings.GEMINI_API_KEY:
                from .gemini_client import GeminiClient
                _client = GeminiClient()
            elif provider == "openai" and settings.OPENAI_API_KEY:
                from .openai_client import OpenAIClient
                _client = OpenAIClient()
            else:
                raise RuntimeError(f"no API key for provider '{provider}'")
    except Exception as e:  # noqa: BLE001
        log.warning("LLM provider unavailable (%s) - using mock", e)
        _client = None
    if _client is None:
        from .mock_client import MockClient
        _client = MockClient()
    return _client


def reset_client() -> None:
    global _client
    _client = None
