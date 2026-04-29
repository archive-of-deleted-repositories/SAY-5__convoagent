# convoagent

Conversational AI customer support agent. Python NLP backend
(intent classification + sentiment analysis + escalation policy) +
TypeScript/React shell. 500-conversation eval harness gates that
the agent auto-resolves ≥70% of cases without escalating to a
human.

```
user ──HTTP──▶ FastAPI ──Agent.step──▶ Intent classifier
                          │             Sentiment scorer
                          │             EscalationPolicy
                          ▼
                    AgentTurn{intent, sentiment,
                              action, response}
                          │
                          ├── HANDLE  ─▶ canned response per intent
                          └── ESCALATE ─▶ human handoff
```

## Versions

| Version | Capability | Status |
|---|---|---|
| v1 | Intent classifier (9 classes) + lexicon-based sentiment + Agent loop with canned responses + ConversationState + FastAPI `/turn` endpoint | shipped |
| v2 | SSE `/stream` endpoint emits `intent` → `sentiment` → `action` → `token` → `done` so a UI renders agent thinking live | shipped |
| v3 | EscalationPolicy with three triggers (sentiment crashed, sustained-negative on high-risk intent, turn budget) + 500-case eval suite gating ≥70% auto-resolve rate | shipped |

## Quickstart

```bash
cd python
pip install -e ".[dev]"
pytest                              # 20 tests
convoagent serve                    # http://127.0.0.1:8000
convoagent eval --n 500             # canonical eval suite
```

## Tests

20 Python tests:
- **intent** (6): keyword matches per class + fallback to OTHER
- **sentiment** (5): positive / negative / neutral, intensifiers, empty
- **policy + agent + eval** (6): handle/escalate paths, policy
  triggers, 200-case eval gate
- **app** (3): /turn endpoint shape, multi-turn session state, SSE
  stream events

Plus a TypeScript `web/` shell with a typed `api.ts` client and a
minimal React `Chat` component.

## What v3's escalation policy buys you

A chatbot that escalates on the wrong signal frustrates users (too
eager to hand off) or fails them (too slow to hand off). The
policy's three triggers cover the cases that matter:

- **Sentiment floor** (default `score ≤ -0.5`): customer is upset
  *now* — don't make them repeat themselves to a bot.
- **Consecutive negative + high-risk intent**: customer is asking
  for a refund or reporting a bug AND has been negative for ≥2
  turns — the bot isn't going to fix this with another canned
  reply.
- **Turn budget** (default 8): conversation has gone too long
  without resolution; cut losses.

The 500-case eval suite ratifies these thresholds: 75% cooperative
flows resolve cleanly, 25% angry flows escalate within 1-2 turns,
overall auto-resolve rate ≥70%.
