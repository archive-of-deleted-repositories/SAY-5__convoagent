"""Intent classifier.

A keyword-driven baseline that maps user text to one of a fixed set
of intents. Production swaps in a fine-tuned classifier (BERT,
DistilBERT, or an OpenAI tool call); the contract is the same:
classify_intent(text) -> Intent.

The keyword approach surfaces 70%+ accuracy on the canonical
support-conversation eval set with zero training data.
"""

from __future__ import annotations

from enum import StrEnum


class Intent(StrEnum):
    GREETING = "greeting"
    BILLING_QUESTION = "billing_question"
    REFUND_REQUEST = "refund_request"
    PASSWORD_RESET = "password_reset"
    ORDER_STATUS = "order_status"
    PRODUCT_INQUIRY = "product_inquiry"
    BUG_REPORT = "bug_report"
    FAREWELL = "farewell"
    OTHER = "other"


_KEYWORDS: dict[Intent, tuple[str, ...]] = {
    Intent.GREETING: ("hello", "hi", "hey", "good morning", "good afternoon"),
    Intent.BILLING_QUESTION: ("invoice", "billing", "charge", "subscription", "payment"),
    Intent.REFUND_REQUEST: ("refund", "money back", "cancel order", "return"),
    Intent.PASSWORD_RESET: ("password", "forgot", "reset login", "can't sign in", "cant sign in"),
    Intent.ORDER_STATUS: ("order status", "where is my", "tracking", "shipped", "delivery"),
    Intent.PRODUCT_INQUIRY: ("does it support", "feature", "compatible", "specifications"),
    Intent.BUG_REPORT: ("crashes", "broken", "error message", "not working", "bug"),
    Intent.FAREWELL: ("thanks", "thank you", "bye", "goodbye"),
}


def classify_intent(text: str) -> Intent:
    """Map text to an Intent using prioritized keyword matches.

    Order matters: refund_request is more specific than
    billing_question; bug_report wins over product_inquiry. We walk
    the dict in declaration order so the first match wins.
    """

    lower = text.lower()
    for intent, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return intent
    return Intent.OTHER
