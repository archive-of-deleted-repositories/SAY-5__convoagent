"""Agent — orchestrates intent + sentiment + policy + canned
responses.

Each turn:
1. Classify intent.
2. Score sentiment.
3. Update conversation state (consecutive-negative counter, turn
   count).
4. Ask the policy what to do.
5. Either generate a canned response (HANDLE) or hand off
   (ESCALATE).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from convoagent.intent import Intent, classify_intent
from convoagent.policy import Action, EscalationPolicy
from convoagent.sentiment import Sentiment, score_sentiment


@dataclass
class ConversationState:
    turn_count: int = 0
    consecutive_negative: int = 0
    history: list[tuple[str, str]] = field(default_factory=list)  # (user, agent)


@dataclass(frozen=True, slots=True)
class AgentTurn:
    user_text: str
    intent: Intent
    sentiment: Sentiment
    action: Action
    response: str
    rationale: str


# Canned responses per intent. Production wraps an LLM call here.
_CANNED: dict[Intent, str] = {
    Intent.GREETING: "Hi! How can I help today?",
    Intent.BILLING_QUESTION: (
        "Happy to help with billing. Could you share the invoice number "
        "or the date of the charge?"
    ),
    Intent.REFUND_REQUEST: (
        "I can start a refund — could you share your order id?"
    ),
    Intent.PASSWORD_RESET: (
        "I'll send a reset link to the email on file. Confirm the email?"
    ),
    Intent.ORDER_STATUS: (
        "Let me look that up. Could you share your order id?"
    ),
    Intent.PRODUCT_INQUIRY: (
        "Glad to help. Which feature or product do you have in mind?"
    ),
    Intent.BUG_REPORT: (
        "Sorry to hear that. What were you doing when the issue happened?"
    ),
    Intent.FAREWELL: "You're welcome — have a great day!",
    Intent.OTHER: "Could you give me a bit more detail on what you need?",
}

_ESCALATE_RESPONSE = (
    "I'm going to bring in a human teammate so we can resolve this faster. "
    "One moment while I transfer you."
)


@dataclass
class Agent:
    policy: EscalationPolicy = field(default_factory=EscalationPolicy)

    def step(self, user_text: str, state: ConversationState) -> AgentTurn:
        intent = classify_intent(user_text)
        sentiment = score_sentiment(user_text)
        if sentiment.label == "negative":
            state.consecutive_negative += 1
        else:
            state.consecutive_negative = 0
        state.turn_count += 1

        decision = self.policy.decide(
            intent=intent,
            sentiment=sentiment,
            consecutive_negative=state.consecutive_negative,
            turn_count=state.turn_count,
        )
        response = (
            _ESCALATE_RESPONSE if decision.action == Action.ESCALATE else _CANNED[intent]
        )
        state.history.append((user_text, response))
        return AgentTurn(
            user_text=user_text,
            intent=intent,
            sentiment=sentiment,
            action=decision.action,
            response=response,
            rationale=decision.rationale,
        )
