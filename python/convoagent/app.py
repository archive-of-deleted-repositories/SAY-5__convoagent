"""FastAPI server with SSE streaming of agent turns."""

from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from convoagent.agent import Agent, ConversationState


class TurnRequest(BaseModel):
    model_config = {"extra": "forbid"}
    text: str = Field(min_length=1)


def create_app() -> FastAPI:
    app = FastAPI(title="convoagent")
    agent = Agent()
    sessions: dict[str, ConversationState] = {}

    def state(sid: str) -> ConversationState:
        s = sessions.get(sid)
        if s is None:
            s = ConversationState()
            sessions[sid] = s
        return s

    @app.post("/session/{sid}/turn")
    def turn(sid: str, req: TurnRequest) -> dict:
        t = agent.step(req.text, state(sid))
        return {
            "intent": t.intent.value,
            "sentiment": {"score": t.sentiment.score, "label": t.sentiment.label},
            "action": t.action.value,
            "response": t.response,
            "rationale": t.rationale,
        }

    @app.get("/session/{sid}/stream")
    def stream(sid: str, text: str) -> StreamingResponse:
        async def gen():
            t = agent.step(text, state(sid))
            yield 'event: intent\ndata: ' + json.dumps({"intent": t.intent.value}) + '\n\n'
            yield (
                'event: sentiment\ndata: '
                + json.dumps({"score": t.sentiment.score, "label": t.sentiment.label})
                + '\n\n'
            )
            yield 'event: action\ndata: ' + json.dumps({"action": t.action.value}) + '\n\n'
            for word in t.response.split():
                yield f'event: token\ndata: {json.dumps(word)}\n\n'
                await asyncio.sleep(0)
            yield 'event: done\ndata: {}\n\n'

        return StreamingResponse(gen(), media_type="text/event-stream")

    return app
