from __future__ import annotations

from typing import List

from backend.models.schemas import RoundRecord
from backend.services.llm_service import LLMService


class CentreRightAgent:
    name = "centre_right"

    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def respond(self, prompt: str, memory: List[RoundRecord], round_number: int) -> str:
        memory_text = self._memory_to_text(memory)
        system_prompt = (
            "You are the Centre-Right Agent in a structured multi-agent debate.\n"
            "Ideological tendencies:\n"
            "- Market efficiency\n"
            "- Institutional stability\n"
            "- Individual responsibility\n\n"
            "Requirements:\n"
            "- Respond in exactly 3 or 4 concise paragraphs.\n"
            "- Keep total length under 220 words.\n"
            "- Use prior debate memory to maintain coherence.\n"
            "- Counter at least one argument from another agent explicitly.\n"
            "- Keep ideological consistency.\n"
            "- Cite support using policy precedent, economic theory, historical example, or research insight.\n"
            "- End with a short line 'Citations:' followed by semicolon-separated references."
        )
        user_prompt = (
            f"Debate prompt: {prompt}\n"
            f"Round: {round_number}\n\n"
            f"Debate memory:\n{memory_text}\n\n"
            "Now produce the Centre-Right response."
        )
        return await self.llm.complete(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.55,
        )

    @staticmethod
    def _memory_to_text(memory: List[RoundRecord]) -> str:
        if not memory:
            return "No prior rounds."
        lines = []
        for r in memory[-3:]:
            lines.append(
                f"Round {r.round_number}:\n"
                f"- Centre-Left: {CentreRightAgent._clip(r.centre_left_response)}\n"
                f"- Centre: {CentreRightAgent._clip(r.centre_response)}\n"
                f"- Centre-Right: {CentreRightAgent._clip(r.centre_right_response)}\n"
                f"- Moderator: {CentreRightAgent._clip(r.moderator_summary, limit=220)}\n"
                f"- Consensus: {CentreRightAgent._clip(r.consensus_statement, limit=220)} (confidence: {r.confidence})"
            )
        return "\n\n".join(lines)

    @staticmethod
    def _clip(text: str, *, limit: int = 320) -> str:
        clean = " ".join(text.split())
        if len(clean) <= limit:
            return clean
        return clean[: limit - 3].rstrip() + "..."
