from __future__ import annotations

from typing import AsyncGenerator, Dict
from uuid import uuid4

from backend.agents.centre import CentreAgent
from backend.agents.centre_left import CentreLeftAgent
from backend.agents.centre_right import CentreRightAgent
from backend.agents.moderator import ModeratorAgent
from backend.memory.memory_store import InMemoryDebateStore
from backend.models.schemas import DebateEvent, DebateStartRequest, RoundRecord
from backend.services.llm_service import LLMService


class DebateEngine:
    def __init__(self) -> None:
        self.store = InMemoryDebateStore()
        self.llm = LLMService()

        self.centre_left = CentreLeftAgent(self.llm)
        self.centre = CentreAgent(self.llm)
        self.centre_right = CentreRightAgent(self.llm)
        self.moderator = ModeratorAgent(self.llm)

    async def run_debate(self, request: DebateStartRequest) -> AsyncGenerator[Dict, None]:
        session_id = str(uuid4())
        yield DebateEvent(
            event_type="started",
            target_confidence=request.confidence_target,
            message="Debate started",
        ).model_dump()

        final_consensus = ""
        final_confidence = 0.0
        rounds_completed = 0

        for round_number in range(1, request.max_rounds + 1):
            history = self.store.get_history(session_id)

            yield DebateEvent(
                event_type="round_start",
                round_number=round_number,
                message=f"Debate Round {round_number} started",
            ).model_dump()

            yield DebateEvent(
                event_type="agent_thinking",
                round_number=round_number,
                agent="centre_left",
                message="Centre-Left agent is thinking...",
            ).model_dump()
            centre_left_response = await self.centre_left.respond(request.prompt, history, round_number)
            yield DebateEvent(
                event_type="agent_response",
                round_number=round_number,
                agent="centre_left",
                content=centre_left_response,
            ).model_dump()

            yield DebateEvent(
                event_type="agent_thinking",
                round_number=round_number,
                agent="centre",
                message="Centre agent is thinking...",
            ).model_dump()
            centre_response = await self.centre.respond(request.prompt, history, round_number)
            yield DebateEvent(
                event_type="agent_response",
                round_number=round_number,
                agent="centre",
                content=centre_response,
            ).model_dump()

            yield DebateEvent(
                event_type="agent_thinking",
                round_number=round_number,
                agent="centre_right",
                message="Centre-Right agent is thinking...",
            ).model_dump()
            centre_right_response = await self.centre_right.respond(request.prompt, history, round_number)
            yield DebateEvent(
                event_type="agent_response",
                round_number=round_number,
                agent="centre_right",
                content=centre_right_response,
            ).model_dump()

            yield DebateEvent(
                event_type="moderator_thinking",
                round_number=round_number,
                agent="moderator",
                message="Moderator is synthesizing the round...",
            ).model_dump()
            moderator_output = await self.moderator.moderate(
                prompt=request.prompt,
                round_number=round_number,
                centre_left_response=centre_left_response,
                centre_response=centre_response,
                centre_right_response=centre_right_response,
                memory=history,
            )
            yield DebateEvent(
                event_type="moderator_response",
                round_number=round_number,
                agent="moderator",
                moderator=moderator_output,
                message=f"Moderator confidence: {moderator_output.confidence:.1f}%",
            ).model_dump()

            record = RoundRecord(
                round_number=round_number,
                centre_left_response=centre_left_response,
                centre_response=centre_response,
                centre_right_response=centre_right_response,
                moderator_summary=moderator_output.summary,
                consensus_statement=moderator_output.consensus_statement,
                confidence=moderator_output.confidence,
            )
            self.store.append_round(session_id, record)

            rounds_completed = round_number
            final_consensus = moderator_output.consensus_statement
            final_confidence = moderator_output.confidence

            yield DebateEvent(
                event_type="round",
                round_number=round_number,
                round_data=record,
                moderator=moderator_output,
            ).model_dump()

            if moderator_output.confidence >= request.confidence_target:
                break

        yield DebateEvent(
            event_type="final",
            final_consensus=final_consensus,
            final_confidence=final_confidence,
            rounds_completed=rounds_completed,
            message="Debate completed",
        ).model_dump()

        self.store.clear(session_id)
