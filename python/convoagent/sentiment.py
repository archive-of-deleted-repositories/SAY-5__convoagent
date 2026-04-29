"""Lexicon-based sentiment scorer.

Returns a score in [-1.0, 1.0]. Negative = upset, positive = happy.
Production swaps in a real model (cardiffnlp/twitter-roberta-base-
sentiment, or an OpenAI sentiment tool call); contract identical.

Lexicon coverage is intentionally narrow — the goal is to get the
sign right (which drives escalation) more than the magnitude.
"""

from __future__ import annotations

from dataclasses import dataclass

_POS = {
    "great", "good", "thanks", "thank", "happy", "love", "perfect",
    "wonderful", "excellent", "appreciate", "helpful", "awesome",
}
_NEG = {
    "bad", "terrible", "awful", "frustrated", "angry", "hate",
    "broken", "useless", "horrible", "disappointed", "worst", "stupid",
    "annoying", "ridiculous",
}
_INTENSIFIERS = {"very", "extremely", "absolutely", "really"}


@dataclass(frozen=True, slots=True)
class Sentiment:
    score: float       # [-1, 1]
    label: str         # "positive" | "neutral" | "negative"


def score_sentiment(text: str) -> Sentiment:
    tokens = [t.strip(".,!?;:").lower() for t in text.split() if t.strip()]
    if not tokens:
        return Sentiment(score=0.0, label="neutral")
    pos = 0
    neg = 0
    intensify = 1.0
    for tok in tokens:
        if tok in _INTENSIFIERS:
            intensify = 1.5
            continue
        if tok in _POS:
            pos += 1 * intensify
        elif tok in _NEG:
            neg += 1 * intensify
        intensify = 1.0
    raw = pos - neg
    # Squash to [-1, 1] using a simple ratio.
    n = max(1, pos + neg)
    score = max(-1.0, min(1.0, raw / n))
    label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    return Sentiment(score=score, label=label)
