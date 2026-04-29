// Typed client for the convoagent Python backend. The shape mirrors
// the FastAPI response so a downstream React component just consumes
// `TurnResponse` directly.

export type Action = "handle" | "escalate" | "defer";
export type SentimentLabel = "positive" | "neutral" | "negative";

export interface SentimentScore {
    score: number;
    label: SentimentLabel;
}

export interface TurnResponse {
    intent: string;
    sentiment: SentimentScore;
    action: Action;
    response: string;
    rationale: string;
}

export interface StreamEvent {
    type: "intent" | "sentiment" | "action" | "token" | "done";
    data: unknown;
}

const DEFAULT_BASE = "http://127.0.0.1:8000";

export async function sendTurn(
    sessionId: string,
    text: string,
    base: string = DEFAULT_BASE,
): Promise<TurnResponse> {
    const res = await fetch(`${base}/session/${encodeURIComponent(sessionId)}/turn`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`turn failed: ${res.status}`);
    return (await res.json()) as TurnResponse;
}

// Subscribe to the SSE stream for a turn. Calls `onEvent` for each
// frame; resolves when the server emits `event: done`.
export async function streamTurn(
    sessionId: string,
    text: string,
    onEvent: (e: StreamEvent) => void,
    base: string = DEFAULT_BASE,
): Promise<void> {
    const url =
        `${base}/session/${encodeURIComponent(sessionId)}/stream?text=` +
        encodeURIComponent(text);
    const res = await fetch(url);
    if (!res.body) throw new Error("no stream body");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        // SSE messages are separated by \n\n.
        let idx;
        while ((idx = buf.indexOf("\n\n")) !== -1) {
            const frame = buf.slice(0, idx);
            buf = buf.slice(idx + 2);
            const lines = frame.split("\n");
            const ev = lines.find((l) => l.startsWith("event: "))?.slice(7);
            const data = lines.find((l) => l.startsWith("data: "))?.slice(6);
            if (!ev || !data) continue;
            try {
                onEvent({ type: ev as StreamEvent["type"], data: JSON.parse(data) });
                if (ev === "done") return;
            } catch {
                // skip malformed
            }
        }
    }
}
