// Minimal React chat shell. Production wraps this in the customer
// support team's existing app shell; this version is intentionally
// small so the typed `api.ts` surface is easy to read.

import { useState } from "react";
import type { Action } from "./api";
import { sendTurn } from "./api";

interface Turn {
    user: string;
    agent: string;
    action: Action;
    rationale: string;
}

export function Chat({ sessionId }: { sessionId: string }): JSX.Element {
    const [turns, setTurns] = useState<Turn[]>([]);
    const [draft, setDraft] = useState("");

    async function send(): Promise<void> {
        const text = draft.trim();
        if (!text) return;
        setDraft("");
        try {
            const res = await sendTurn(sessionId, text);
            setTurns((prev) => [
                ...prev,
                {
                    user: text,
                    agent: res.response,
                    action: res.action,
                    rationale: res.rationale,
                },
            ]);
        } catch (err) {
            setTurns((prev) => [
                ...prev,
                {
                    user: text,
                    agent: `[error: ${String(err)}]`,
                    action: "handle",
                    rationale: "",
                },
            ]);
        }
    }

    return (
        <div className="convo">
            <ol className="turns">
                {turns.map((t, i) => (
                    <li key={i} className={`turn turn--${t.action}`}>
                        <div className="user">{t.user}</div>
                        <div className="agent">{t.agent}</div>
                        {t.action === "escalate" && (
                            <div className="badge">Escalating: {t.rationale}</div>
                        )}
                    </li>
                ))}
            </ol>
            <div className="composer">
                <input
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") void send();
                    }}
                    placeholder="how can I help?"
                />
                <button onClick={() => void send()}>send</button>
            </div>
        </div>
    );
}
