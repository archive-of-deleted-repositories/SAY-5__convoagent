"""500-conversation eval harness.

Each `EvalCase` is (conversation_id, turns, expected_outcome). The
runner walks the turns through the agent, records what happened,
and aggregates: how many were resolved without escalation? How
many escalated correctly (the case expected escalation)?

The headline metric is the "auto-resolve rate" — fraction of cases
where the agent reached a non-escalated terminal state. The
canonical eval set targets ≥ 70%.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from convoagent.agent import Agent, ConversationState
from convoagent.policy import Action

Expected = Literal["resolve", "escalate"]


@dataclass(frozen=True, slots=True)
class EvalCase:
    id: str
    turns: tuple[str, ...]
    expected: Expected


@dataclass(frozen=True, slots=True)
class EvalReport:
    total: int
    resolved: int
    escalated: int
    correct_escalations: int
    auto_resolve_rate: float


@dataclass
class EvalSuite:
    cases: list[EvalCase] = field(default_factory=list)


def generate_canonical_suite(n: int = 500, seed: int = 17) -> EvalSuite:
    """Build a deterministic synthetic suite. Half are cooperative
    happy-path conversations (expected: resolve); a quarter are
    high-risk (expected: escalate); a quarter are mixed."""

    rng = random.Random(seed)
    cooperative = [
        ("hi there",),
        ("hi i forgot my password",),
        ("where is my order",),
        ("does it support python 3.11?", "thanks!"),
        ("hello — got an invoice question",),
    ]
    angry = [
        ("this is broken and i'm angry",),
        ("the app crashes constantly i hate this",),
        ("i want a refund this is terrible",),
        ("absolutely useless. refund please",),
    ]
    cases: list[EvalCase] = []
    for i in range(n):
        if i % 4 == 0:
            turns = rng.choice(angry)
            expected: Expected = "escalate"
        else:
            turns = rng.choice(cooperative)
            expected = "resolve"
        cases.append(EvalCase(id=f"c-{i:04d}", turns=turns, expected=expected))
    return EvalSuite(cases=cases)


def run_eval(suite: EvalSuite, agent: Agent | None = None) -> EvalReport:
    a = agent or Agent()
    resolved = 0
    escalated = 0
    correct_escalations = 0
    for case in suite.cases:
        state = ConversationState()
        outcome: Action = Action.HANDLE
        for utter in case.turns:
            t = a.step(utter, state)
            outcome = t.action
            if outcome == Action.ESCALATE:
                break
        if outcome == Action.ESCALATE:
            escalated += 1
            if case.expected == "escalate":
                correct_escalations += 1
        else:
            resolved += 1
    auto_resolve = resolved / len(suite.cases) if suite.cases else 0.0
    return EvalReport(
        total=len(suite.cases),
        resolved=resolved,
        escalated=escalated,
        correct_escalations=correct_escalations,
        auto_resolve_rate=auto_resolve,
    )
