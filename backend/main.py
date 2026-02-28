from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.debate_engine import DebateEngine
from backend.models.schemas import DebateStartRequest

app = FastAPI(title="Multi-Agent Debate API", version="1.0.0")
engine = DebateEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/start-debate")
async def start_debate(request: DebateStartRequest) -> StreamingResponse:
    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in engine.run_debate(request):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            error_event = {
                "event_type": "error",
                "message": f"Debate failed: {str(exc)}",
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
