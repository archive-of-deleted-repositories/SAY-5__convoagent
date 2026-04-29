from __future__ import annotations

from fastapi.testclient import TestClient

from convoagent import create_app


def test_turn_endpoint_returns_full_breakdown() -> None:
    c = TestClient(create_app())
    r = c.post("/session/u1/turn", json={"text": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "greeting"
    assert body["action"] == "handle"
    assert "Hi" in body["response"] or "hi" in body["response"].lower()


def test_session_state_persists_across_turns() -> None:
    """Verify that ConversationState carries across requests by
    looking at the turn budget. Default budget is 8 turns; the 8th
    cooperative turn should be the first to escalate."""

    c = TestClient(create_app())
    # First 7 turns: HANDLE.
    for _ in range(7):
        r = c.post("/session/u-budget/turn", json={"text": "hi just chatting"}).json()
        assert r["action"] == "handle"
    # 8th turn trips the budget threshold (>= 8).
    r = c.post("/session/u-budget/turn", json={"text": "hi just chatting"}).json()
    assert r["action"] == "escalate"
    assert "budget" in r["rationale"].lower() or "turn" in r["rationale"].lower()


def test_stream_endpoint_emits_intent_sentiment_action_token_done() -> None:
    c = TestClient(create_app())
    with c.stream("GET", "/session/u1/stream?text=hello") as resp:
        body = b"".join(resp.iter_bytes()).decode()
    for ev in ("intent", "sentiment", "action", "token", "done"):
        assert f"event: {ev}\n" in body
