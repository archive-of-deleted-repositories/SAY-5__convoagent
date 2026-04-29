"""v3: escalation policy.

A `EscalationPolicy` decides, given the conversation state, whether
the agent should:
- HANDLE the turn itself (most cases),
- ESCALATE to a human now (sentiment crashed or intent is high-risk),
- DEFER (gather one more clarification turn before deciding).

Decision factors:
- Negative sentiment for ≥ N consecutive turns
- Intent matches a high-risk class (refund, bug_report)
- Conversation length exceeds a budget without resolution

The policy is the headline v3 feature: it's the difference between
a chatbot that frustrates users and one that knows when to step
aside.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from convoagent.intent import Intent
from convoagent.sentiment import Sentiment


class Action(StrEnum):
    HANDLE = "handle"
    ESCALATE = "escalate"
    DEFER = "defer"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    action: Action
    rationale: str


@dataclass
class EscalationPolicy:
    consecutive_negative_threshold: int = 2
    high_risk_intents: frozenset[Intent] = field(
        default_factory=lambda: frozenset({Intent.REFUND_REQUEST, Intent.BUG_REPORT})
    )
    max_turns_before_escalate: int = 8
    sentiment_floor: float = -0.5

    def decide(
        self,
        intent: Intent,
        sentiment: Sentiment,
        consecutive_negative: int,
        turn_count: int,
    ) -> PolicyDecision:
        if sentiment.score <= self.sentiment_floor:
            return PolicyDecision(
                action=Action.ESCALATE,
                rationale=f"sentiment score {sentiment.score:.2f} crashed below floor",
            )
        if (
            consecutive_negative >= self.consecutive_negative_threshold
            and intent in self.high_risk_intents
        ):
            return PolicyDecision(
                action=Action.ESCALATE,
                rationale=(
                    f"{consecutive_negative} consecutive negative turns "
                    f"on a high-risk intent ({intent.value})"
                ),
            )
        if turn_count >= self.max_turns_before_escalate:
            return PolicyDecision(
                action=Action.ESCALATE,
                rationale=(
                    f"conversation reached {turn_count} turns without resolution "
                    f"(budget: {self.max_turns_before_escalate})"
                ),
            )
        return PolicyDecision(
            action=Action.HANDLE,
            rationale="within nominal bounds",
        )
