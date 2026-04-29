"""CLI: `convoagent serve` runs the FastAPI server. `convoagent eval`
runs the canonical 500-conversation suite."""

from __future__ import annotations

import sys

from convoagent.eval import generate_canonical_suite, run_eval


def _serve(args: list[str]) -> int:
    import uvicorn

    from convoagent import create_app

    host = "127.0.0.1"
    port = 8000
    a = iter(args)
    for tok in a:
        if tok == "--host":
            host = next(a, host)
        elif tok == "--port":
            port = int(next(a, str(port)))
    uvicorn.run(create_app(), host=host, port=port)
    return 0


def _eval(args: list[str]) -> int:
    n = 500
    a = iter(args)
    for tok in a:
        if tok == "--n":
            n = int(next(a, str(n)))
    suite = generate_canonical_suite(n=n)
    rep = run_eval(suite)
    print(f"total          : {rep.total}")
    print(f"resolved       : {rep.resolved}")
    print(f"escalated      : {rep.escalated}")
    print(f"correct escal. : {rep.correct_escalations}")
    print(f"auto-resolve % : {rep.auto_resolve_rate * 100:.1f}")
    return 0 if rep.auto_resolve_rate >= 0.65 else 1


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: convoagent {serve|eval} ...", file=sys.stderr)
        return 2
    cmd, rest = args[0], args[1:]
    if cmd == "serve":
        return _serve(rest)
    if cmd == "eval":
        return _eval(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
