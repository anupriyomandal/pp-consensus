from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DebateStartRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=3000)
    confidence_target: float = Field(..., ge=0, le=100)
    max_rounds: int = Field(default=8, ge=1, le=20)


class AgentOutput(BaseModel):
    agent: Literal["centre_left", "centre", "centre_right"]
    response: str
    citations: List[str] = Field(default_factory=list)


class ModeratorOutput(BaseModel):
    agreements: List[str] = Field(default_factory=list)
    disagreements: List[str] = Field(default_factory=list)
    strongest_arguments: List[str] = Field(default_factory=list)
    consensus_statement: str
    confidence: float = Field(..., ge=0, le=100)
    summary: str


class RoundRecord(BaseModel):
    round_number: int
    centre_left_response: str
    centre_response: str
    centre_right_response: str
    moderator_summary: str
    consensus_statement: str
    confidence: float


class DebateEvent(BaseModel):
    event_type: Literal[
        "started",
        "round_start",
        "agent_thinking",
        "agent_response",
        "moderator_thinking",
        "moderator_response",
        "round",
        "final",
        "error",
    ]
    round_number: Optional[int] = None
    agent: Optional[Literal["centre_left", "centre", "centre_right", "moderator"]] = None
    content: Optional[str] = None
    target_confidence: Optional[float] = None
    round_data: Optional[RoundRecord] = None
    moderator: Optional[ModeratorOutput] = None
    final_consensus: Optional[str] = None
    final_confidence: Optional[float] = None
    rounds_completed: Optional[int] = None
    message: Optional[str] = None
