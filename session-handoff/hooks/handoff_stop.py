#!/usr/bin/env python3
"""Stop hook: ask Claude to update HANDOFF.md before it stops.

Claude Code has no session-end event that can still run the model (SessionEnd
hooks are shell-only), so this runs on Stop, which fires at the end of every
turn. It only blocks when the session has used a tool that changes things
(Edit, Write, MultiEdit, NotebookEdit, Bash) since HANDOFF.md was last written.
Q&A-only turns stop normally, and so does the turn where Claude writes the note.
"""
import json
import os
import sys
from datetime import datetime

WORK_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "Bash"}


def parse_ts(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return None


def work_since(transcript_path, since):
    """True if the transcript has a work tool call newer than `since`."""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                ts = parse_ts(entry.get("timestamp"))
                if ts is None or ts <= since:
                    continue
                content = (entry.get("message") or {}).get("content") or []
                for block in content if isinstance(content, list) else []:
                    if block.get("type") == "tool_use" and block.get("name") in WORK_TOOLS:
                        return True
    except OSError:
        return False
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if data.get("stop_hook_active"):
        return 0

    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    handoff = os.path.join(root, "HANDOFF.md")
    since = os.path.getmtime(handoff) if os.path.exists(handoff) else 0

    if not work_since(data.get("transcript_path", ""), since):
        return 0

    session = (data.get("session_id") or "")[:8]
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    reason = (
        f"Before stopping, update {handoff} (session-handoff skill). "
        "Keep it under about 40 lines and overwrite anything stale. "
        f"Start with '# Handoff' and 'Updated: {now.strftime('%Y-%m-%d %H:%M')}'. Sections: "
        "Where we stopped, Done, Next, Open decisions / blockers, Key files. "
        "At the bottom keep '## Previous sessions' with one line per session, newest first: "
        f"'- {today} ({session}): <what this session did>'. "
        f"If a line for {session} already exists, rewrite it instead of adding another. "
        "Write the file, then stop. Don't summarize it back to the user."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
