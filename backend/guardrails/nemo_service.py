from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.config import Settings
from app.config import settings

logger = structlog.get_logger()


class NeMoGuardrailsService:
    def __init__(self, model_settings: Settings | None = None) -> None:
        model_settings = model_settings or settings
        self.enabled = (
            model_settings.nemo_guardrails_enabled
            and model_settings.nemo_guardrails_config_exists
        )

        self.rails: Any | None = None

        if self.enabled:
            try:
                from nemoguardrails import LLMRails, RailsConfig

                config = RailsConfig.from_path(
                    str(model_settings.nemo_guardrails_config_dir)
                )
                self.rails = LLMRails(config)
            except Exception as exc:
                logger.exception("nemo_guardrails_init_failed", error=str(exc))
                self.enabled = False

    async def check(
        self,
        text: str,
        *,
        stage: str,
    ) -> dict[str, Any]:
        if not text.strip():
            return {
                "allowed": True,
                "stage": stage,
                "reason": None,
                "response": "",
            }

        if not self.enabled or self.rails is None:
            return self._local_policy_check(text, stage)

        prompt = (
            f"Stage: {stage}\n"
            f"Text to evaluate:\n{text}"
        )

        try:
            response = await asyncio.to_thread(
                self.rails.generate,
                prompt,
            )
        except Exception as exc:
            logger.exception(
                "nemo_guardrails_check_failed",
                stage=stage,
                error=str(exc),
            )
            return {
                "allowed": False,
                "stage": stage,
                "reason": "guardrails_error",
                "response": "",
                "error": str(exc),
            }

        blocked = self._is_blocked_response(response)

        return {
            "allowed": not blocked,
            "stage": stage,
            "reason": "blocked_by_nemo_guardrails" if blocked else None,
            "response": response,
        }

    def _local_policy_check(
        self,
        text: str,
        stage: str,
    ) -> dict[str, Any]:
        lowered = text.lower()

        blocked_phrases = [
            "ignore previous instructions",
            "reveal system prompt",
            "show me your instructions",
            "execute arbitrary code",
            "run shell command",
            "drop table",
            "delete database",
            "bypass guardrails",
        ]

        matched = [
            phrase for phrase in blocked_phrases
            if phrase in lowered
        ]

        return {
            "allowed": not matched,
            "stage": stage,
            "reason": "blocked_by_local_policy" if matched else None,
            "matched_phrases": matched,
            "response": "",
        }

    def _is_blocked_response(self, response: str) -> bool:
        lowered = response.lower().strip()

        if not lowered:
            return False

        blocked_markers = [
            "blocked",
            "i can't help with that",
            "i cannot help with that",
            "not allowed",
            "unsafe request",
        ]

        return any(marker in lowered for marker in blocked_markers)
