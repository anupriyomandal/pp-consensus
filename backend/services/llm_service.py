from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI


class LLMService:
    def __init__(self) -> None:
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self._client = AsyncOpenAI(api_key=self.api_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.5,
        max_tokens: int = 900,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self._client:
            return self._fallback(messages)

        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
        }
        if response_format is not None:
            params["response_format"] = response_format

        try:
            response = await self._client.chat.completions.create(**params)
            return response.choices[0].message.content or ""
        except Exception as exc:
            # Compatibility fallback for models/endpoints that still expect max_tokens.
            if "max_completion_tokens" in str(exc):
                params.pop("max_completion_tokens", None)
                params["max_tokens"] = max_tokens
                response = await self._client.chat.completions.create(**params)
                return response.choices[0].message.content or ""
            raise

    def _fallback(self, messages: List[Dict[str, str]]) -> str:
        prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                prompt = m.get("content", "")
                break

        if '"confidence"' in prompt and '"consensus_statement"' in prompt:
            payload = {
                "agreements": [
                    "All agents agree the decision should be evidence-based.",
                    "All agents acknowledge implementation tradeoffs.",
                ],
                "disagreements": [
                    "The extent of market intervention remains contested.",
                    "The timeline for policy impact is debated.",
                ],
                "strongest_arguments": [
                    "Balancing efficiency with social resilience lowers systemic risk.",
                    "Policy sequencing is critical to avoid unintended consequences.",
                ],
                "consensus_statement": "A phased, evidence-led approach with measurable safeguards is preferred.",
                "confidence": 62.0,
                "summary": "Preliminary convergence exists, but unresolved scope differences reduce confidence.",
            }
            return json.dumps(payload)

        return (
            "This is a fallback response because OPENAI_API_KEY is not configured.\n\n"
            "The argument supports a measured path with explicit tradeoff analysis and cites\n"
            "policy precedent, economic theory, and historical analogs to justify recommendations.\n\n"
            "Counterpoint: a competing stance overweights one objective and underestimates second-order effects.\n\n"
            "References: post-2008 macroprudential reforms; welfare economics; comparative OECD outcomes."
        )
