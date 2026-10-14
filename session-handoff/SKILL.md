---
name: session-handoff
description: Keep a HANDOFF.md in the project root so every session can start fresh instead of using `claude --resume`. Use at the start of a session when HANDOFF.md exists (read it first), when a session is ending or the user says "wrap up", "hand off", "save where we are", or "I'm done for today", and whenever a Stop hook asks you to update HANDOFF.md.
---

# Session handoff

Resuming a cold session re-reads the whole transcript without the prompt cache, which burns usage. A short note in `HANDOFF.md` gives a new session the same footing for a fraction of the tokens.

## At session start

If `HANDOFF.md` exists in the project root, read it before doing anything else. Pick up from "Where we stopped" and "Next" unless the user asks for something different. Check that files it names still exist before relying on them.

## At session end

Write or update `HANDOFF.md` in the project root. Use this shape:

```markdown
# Handoff

Updated: 2026-10-14 16:40

## Where we stopped
One or two sentences: the exact point work paused, mid-task if it was.

## Done
- What this session finished, with commit SHAs or test results when there are any.

## Next
- The next concrete step first. Enough detail that a cold session can start without asking.

## Open decisions / blockers
- Questions waiting on the user, failing tests, missing access. "None" if none.

## Key files
- `path/to/file`: what changed or why it matters.

## Previous sessions
- 2026-10-14 (a1b2c3d4): Added login form; next is the session cookie.
- 2026-10-13 (9f8e7d6c): Scaffolded the app and the test runner.
```

Rules:

- Keep it under about 40 lines. It's a note for the next session.
- Overwrite. Every section above "Previous sessions" describes the state right now. Delete anything that's no longer true.
- "Previous sessions" is the only history: one line per session, newest first. If this session already has a line, rewrite that line. Use the session id the Stop hook gives you; without the hook, use the date.
- Don't paste code, logs, or long diffs. Point to the file or commit.
- Don't put secrets in it.
- After writing it, stop. Don't repeat the note back to the user.

## Hooks

`hooks/handoff_stop.py` is a Stop hook. Claude Code has no end-of-session event that can still run the model (SessionEnd hooks only run shell commands), so it fires at the end of each turn and asks you to update the note only when the session has used Edit, Write, MultiEdit, NotebookEdit, or Bash since `HANDOFF.md` was last written. `hooks/handoff_start.py` is a SessionStart hook that loads `HANDOFF.md` into context on startup, `/clear`, and compaction. Setup is in the repo README.

Without hooks, one line in `CLAUDE.md` does most of the job:

```markdown
Read HANDOFF.md at the start; update it before ending.
```
