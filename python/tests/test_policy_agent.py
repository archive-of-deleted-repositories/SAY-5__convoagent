from __future__ import annotations

from convoagent import (
    Action,
    Agent,
    ConversationState,
    EscalationPolicy,
    EvalSuite,
    run_eval,
)
from convoagent.eval import generate_canonical_suite


def test_agent_handles_greeting_without_escalation() -> None:
    a = Agent()
    s = ConversationState()
    t = a.step("hi there", s)
    assert t.action == Action.HANDLE
    assert "Hi" in t.response or "hi" in t.response.lower()


def test_agent_escalates_on_crashed_sentiment() -> None:
    a = Agent()
    s = ConversationState()
    t = a.step("this is absolutely terrible and broken", s)
    assert t.action == Action.ESCALATE


def test_agent_escalates_after_consecutive_negative_on_high_risk_intent() -> None:
    pol = EscalationPolicy(consecutive_negative_threshold=2)
    a = Agent(policy=pol)
    s = ConversationState()
    a.step("this is a bug", s)
    a.step("the bug is annoying", s)
    t = a.step("the bug is broken", s)
    assert t.action == Action.ESCALATE


def test_agent_escalates_when_turn_budget_exceeded() -> None:
    pol = EscalationPolicy(max_turns_before_escalate=2, sentiment_floor=-0.99)
    a = Agent(policy=pol)
    s = ConversationState()
    for _ in range(2):
        a.step("hello, just chatting", s)
    t = a.step("hello, just chatting", s)
    assert t.action == Action.ESCALATE


def test_canonical_eval_meets_auto_resolve_target() -> None:
    suite = generate_canonical_suite(n=200)
    rep = run_eval(suite)
    # The canonical suite has 75% cooperative + 25% angry → expected
    # auto-resolve ~ 75%. We give a 5pp buffer for tweak-resilience.
    assert rep.auto_resolve_rate >= 0.70


def test_empty_suite_returns_zero_rate() -> None:
    rep = run_eval(EvalSuite(cases=[]))
    assert rep.total == 0
    assert rep.auto_resolve_rate == 0.0
