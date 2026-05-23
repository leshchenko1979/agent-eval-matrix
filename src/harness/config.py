from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider


@dataclass(frozen=True)
class ModelPreset:
    model_name: str
    base_url: str
    api_key_env: str


MODEL_PRESETS: dict[str, ModelPreset] = {
    "minimax-m2.7": ModelPreset(
        model_name="MiniMax-M2.7",
        base_url="https://api.minimax.io/v1",
        api_key_env="MINIMAX_API_KEY",
    ),
}


def get_model(model_id: str) -> OpenAIChatModel:
    preset = MODEL_PRESETS.get(model_id)
    if preset is None:
        raise ValueError(f"Unknown model_id '{model_id}'. Known: {list(MODEL_PRESETS)}")

    api_key = os.environ.get(preset.api_key_env)
    if not api_key:
        raise ValueError(
            f"Missing API key env var {preset.api_key_env!r} for model {model_id!r}"
        )

    base_url = os.getenv("OPENAI_BASE_URL", preset.base_url).rstrip("/")
    model_name = os.getenv("HARNESS_MODEL", preset.model_name)

    return OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(base_url=base_url, api_key=api_key),
    )
