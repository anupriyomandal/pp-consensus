from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from backend.models.schemas import RoundRecord


class InMemoryDebateStore:
    """Simple in-memory store; replace with Redis for distributed deployments."""

    def __init__(self) -> None:
        self._store: Dict[str, List[RoundRecord]] = defaultdict(list)

    def append_round(self, session_id: str, record: RoundRecord) -> None:
        self._store[session_id].append(record)

    def get_history(self, session_id: str) -> List[RoundRecord]:
        return self._store.get(session_id, [])

    def clear(self, session_id: str) -> None:
        if session_id in self._store:
            del self._store[session_id]
