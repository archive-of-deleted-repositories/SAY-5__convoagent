from __future__ import annotations

from convoagent import Intent, classify_intent


def test_greeting_classified() -> None:
    assert classify_intent("hello there") == Intent.GREETING


def test_billing_classified() -> None:
    assert classify_intent("I have a billing question about my invoice") == Intent.BILLING_QUESTION


def test_refund_classified() -> None:
    assert classify_intent("I need a refund for my order") == Intent.REFUND_REQUEST


def test_password_reset_classified() -> None:
    assert classify_intent("I forgot my password and can't sign in") == Intent.PASSWORD_RESET


def test_bug_classified() -> None:
    assert classify_intent("the app crashes when I open settings") == Intent.BUG_REPORT


def test_falls_back_to_other() -> None:
    assert classify_intent("xyzzy plugh") == Intent.OTHER
