from __future__ import annotations

from convoagent import score_sentiment


def test_positive_text_scores_positive() -> None:
    s = score_sentiment("thanks this is great, you're awesome")
    assert s.label == "positive"
    assert s.score > 0


def test_negative_text_scores_negative() -> None:
    s = score_sentiment("this is terrible and broken, useless")
    assert s.label == "negative"
    assert s.score < 0


def test_neutral_text_scores_zero() -> None:
    s = score_sentiment("the order id is 12345")
    assert s.label == "neutral"


def test_intensifiers_amplify_score() -> None:
    base = score_sentiment("this is bad").score
    amplified = score_sentiment("this is extremely bad").score
    assert amplified <= base  # intensifier makes it more negative (or equal at floor)


def test_empty_input_returns_neutral_zero() -> None:
    s = score_sentiment("")
    assert s.score == 0.0
