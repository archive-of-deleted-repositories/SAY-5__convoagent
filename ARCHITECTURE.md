# Architecture

## Layer cake

```
┌───────────────────────────────────────────┐
│  React shell (TypeScript)                │
│  - sendTurn / streamTurn over fetch       │
│  - typed TurnResponse / StreamEvent       │
├───────────────────────────────────────────┤
│  FastAPI                                  │
│  - POST /session/{sid}/turn              │
│  - GET  /session/{sid}/stream             │
├───────────────────────────────────────────┤
│  Agent                                    │
│  - intent classifier (keyword baseline)   │
│  - sentiment scorer (lexicon baseline)    │
│  - escalation policy                      │
│  - canned per-intent responses            │
├───────────────────────────────────────────┤
│  ConversationState                        │
│  - turn_count                             │
│  - consecutive_negative                   │
│  - history                                │
└───────────────────────────────────────────┘
```

## Why baselines, not big models

The headline metric — auto-resolve rate ≥ 70% — is achievable with
keyword + lexicon baselines on the canonical conversation set. That
keeps:

- CI hermetic (no API keys, no model weights)
- Tests deterministic (same input → same output)
- Latency predictable (sub-millisecond per turn vs hundreds of ms
  for a real LLM call)

Production swaps in fine-tuned classifiers (DistilBERT for intent,
cardiffnlp/twitter-roberta-base-sentiment for sentiment) or LLM
tool calls. The Agent surface — `step(text, state) -> AgentTurn` —
doesn't change.

## EscalationPolicy (v3)

Three triggers, in priority order:

1. **Sentiment floor.** If `sentiment.score <= sentiment_floor`
   (default -0.5), escalate immediately. This catches customers
   who arrive already upset; making them repeat to a bot is the
   wrong move.
2. **Consecutive-negative on high-risk intent.** If the user has
   been negative for `consecutive_negative_threshold` turns AND
   the intent is in `high_risk_intents` (default REFUND, BUG),
   escalate. The bot can't talk a frustrated user out of a
   refund.
3. **Turn budget.** If the conversation has gone
   `max_turns_before_escalate` turns (default 8) without
   resolving, escalate. Keeps the agent from trapping customers
   in a loop.

All three are tunable per-deployment. A high-touch luxury brand
might lower the budget to 4; a self-service SaaS might raise it
to 15.

## 500-conversation eval suite

`generate_canonical_suite(n)` produces a deterministic synthetic
mix: 75% cooperative (greeting / billing / order-status / product
inquiry / password reset) + 25% angry (bug-report-with-frustration
/ refund-with-anger). The mix is the worst-case for a baseline
chatbot — angry refund flows are where escalation policies prove
their worth.

`run_eval(suite)` reports:
- `auto_resolve_rate`: fraction of cases that reached a non-
  escalated terminal state
- `correct_escalations`: of the cases that DID escalate, how many
  were *expected* to (precision check on the policy)

The CI gate fails if `auto_resolve_rate < 0.65` (5pp buffer below
the 70% target so policy tweaks have room without breaking
the build).

## Streaming

`/session/{sid}/stream?text=...` emits five SSE event types in
order:

- `event: intent` — classifier verdict (lets the UI dim irrelevant
  knowledge-base entries)
- `event: sentiment` — score + label
- `event: action` — handle | escalate (lets the UI render an
  escalation banner before the response streams)
- `event: token` — one frame per word of generated response
- `event: done` — sentinel

The frame shape matches the rest of the SAY-5 portfolio so a
single subscriber can consume convoagent + clinicalrag + others.
