"""v4: per-session conversation memory.

The Agent (v1) treats every turn in isolation: same intent
classifier, same canned response. v4 adds Memory: as the user
shares facts (their order id, their email, the bug version), we
extract + store them so subsequent turns reference them without
asking again. 'I told you my order id was 42 already' is the kind
of frustration this prevents.

We extract by simple regex patterns. Production swaps in NER /
LLM extraction; the contract — `extract(text) → dict[str, str]`
— stays.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
    "order_id": re.compile(r"\b(?:order|ord|#)\s*#?\s*([A-Z0-9-]{4,})\b", re.IGNORECASE),
    "version": re.compile(r"\b(?:v|version)\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?)\b", re.IGNORECASE),
    "phone": re.compile(r"\b(\+?\d[\d\s().-]{8,}\d)\b"),
}


def extract(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, pat in _PATTERNS.items():
        if m := pat.search(text):
            out[name] = m.group(1)
    return out


@dataclass
class Memory:
    """Per-session keyed store. Updates take the latest value
    (later mentions overwrite earlier — users sometimes correct
    themselves)."""

    facts: dict[str, str] = field(default_factory=dict)

    def update_from(self, text: str) -> dict[str, str]:
        new_facts = extract(text)
        self.facts.update(new_facts)
        return new_facts

    def has(self, key: str) -> bool:
        return key in self.facts

    def get(self, key: str) -> str | None:
        return self.facts.get(key)

    def render(self) -> str:
        """Compact human-readable summary for prompt injection or
        debug logs."""
        if not self.facts:
            return "(no facts captured)"
        return ", ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
