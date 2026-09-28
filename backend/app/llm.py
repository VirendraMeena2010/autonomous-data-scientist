from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

from app.config import settings

def get_chat_model() -> BaseLanguageModel:
    if settings.model_provider != "openai":
        raise RuntimeError(f"Unsupported model provider: {settings.model_provider}")

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required")

    return ChatOpenAI(
        model=settings.model_name,
        temperature=settings.model_temperature,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url if hasattr(settings, "openai_base_url") else None,
    )