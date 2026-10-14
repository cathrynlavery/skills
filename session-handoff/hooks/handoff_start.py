#!/usr/bin/env python3
"""SessionStart hook: load HANDOFF.md into a fresh session's context."""
import json
import os
import sys

MAX_CHARS = 8000


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        data = {}
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    handoff = os.path.join(root, "HANDOFF.md")
    if not os.path.isfile(handoff):
        return 0
    with open(handoff, encoding="utf-8", errors="replace") as f:
        note = f.read(MAX_CHARS + 1)
    if len(note) > MAX_CHARS:
        note = note[:MAX_CHARS] + "\n[truncated; read the full file]"
    context = (
        f"HANDOFF.md from the last session ({handoff}). "
        "Pick up from 'Where we stopped' and 'Next' unless the user asks for something else.\n\n"
        + note
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
