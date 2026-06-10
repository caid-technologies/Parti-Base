"""OpenAI-SDK-compatible client pointed at a local Ollama server.

Ollama exposes `/v1/chat/completions` on `localhost:11434/v1`. Two helpers:
- `chat_text(messages, ...)`           → free-form string response
- `chat_json(messages, schema, ...)`   → JSON object matching `schema`,
  using Ollama's structured-output support. We pass the JSON schema via
  `extra_body={"format": schema}`, which Ollama's OpenAI-compat layer maps
  to its native grammar-constrained sampling. Without a schema we fall
  back to plain JSON-object mode.
"""
from __future__ import annotations
import json
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import (
    OLLAMA_BASE_URL, OLLAMA_API_KEY, MODEL_ID,
    TEMPERATURE, TOP_P, MAX_TOKENS,
)

_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)


@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(4), reraise=True)
def chat_text(
    messages: list[dict],
    temperature: float = TEMPERATURE,
    top_p: float = TOP_P,
    max_tokens: int = MAX_TOKENS,
) -> str:
    resp = _client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


@retry(wait=wait_exponential(min=1, max=20), stop=stop_after_attempt(4), reraise=True)
def chat_json(
    messages: list[dict],
    schema: dict[str, Any] | None = None,
    temperature: float = TEMPERATURE,
    top_p: float = TOP_P,
    max_tokens: int = MAX_TOKENS,
) -> Any:
    extra_body: dict[str, Any] = {}
    if schema is not None:
        extra_body["format"] = schema

    resp = _client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        extra_body=extra_body or None,
    )
    raw = resp.choices[0].message.content or ""
    return json.loads(raw)
