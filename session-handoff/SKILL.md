---
name: session-handoff
description: Maintains HANDOFF.md in the project root so a new session can start fresh with full context instead of using `claude --resume`. Use when a session starts and HANDOFF.md exists, when the user says "wrap up", "save where we are", "I'm done for today", or "pick up where we left off", and when a Stop hook asks for a HANDOFF.md update. Not for briefing a different agent or person; use a handover prompt for that.
---

# Session handoff

Resuming a cold session re-reads the whole transcript without the prompt cache, which burns usage. A short note in `HANDOFF.md` gives a new session the same footing for a fraction of the tokens.

## When not to use

- Handing work to a different agent or a person. They need a brief written for them.
- Throwaway sessions outside a project, such as a one-off question in your home directory.

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

## Excuses to ignore

| Excuse | Why it's wrong |
| --- | --- |
| "Nothing much changed." | If you edited a file or ran a command, the next session needs to know. A one-line update is enough. |
| "The user can resume this session." | Resuming a cold session is the cost this skill exists to avoid. |
| "The git log already says what happened." | Git doesn't record what's next, what's blocked, or what the user still has to decide. |
| "I'll keep the old sections and add a new one." | Stale status reads as current to the next session. Overwrite it. |

## Red flags

- Pasted logs, stack traces, or code blocks in the note.
- "Where we stopped" describes an earlier state than the code.
- Two "Previous sessions" lines for the same session id.
- "Next" says "continue working" instead of naming a step.

## Before you stop

- [ ] Under about 40 lines.
- [ ] "Where we stopped" names an exact point.
- [ ] "Next" starts with a concrete action.
- [ ] Every file under "Key files" exists.
- [ ] One "Previous sessions" line for this session, at the top.

## Hooks

`hooks/handoff_stop.py` is a Stop hook. Claude Code has no end-of-session event that can still run the model (SessionEnd hooks only run shell commands), so it fires at the end of each turn and asks you to update the note only when the session has used Edit, Write, MultiEdit, NotebookEdit, or Bash since `HANDOFF.md` was last written. `hooks/handoff_start.py` is a SessionStart hook that loads `HANDOFF.md` into context on startup, `/clear`, and compaction. `hooks/test_hooks.py` tests both. Setup is in the repo README.

Without hooks, one line in `CLAUDE.md` does most of the job:

```markdown
Read HANDOFF.md at the start; update it before ending.
```
