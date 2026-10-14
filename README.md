# skills

My Claude Code skills, one folder per skill.

| Skill | What it does | Install |
| --- | --- | --- |
| [session-handoff](session-handoff/) | Keeps a `HANDOFF.md` in the project root so each new session starts with full context and you never need `claude --resume`. | `npx skills add cathrynlavery/skills --skill session-handoff -a claude-code -g` |

## Install

All skills:

```bash
npx skills add cathrynlavery/skills --skill '*' -a claude-code -g
```

One skill:

```bash
npx skills add cathrynlavery/skills --skill session-handoff -a claude-code -g
```

`-g` installs to `~/.claude/skills/` for every project. Drop it to install into the current project's `.claude/skills/` instead. This uses the [skills CLI](https://github.com/vercel-labs/skills).

## session-handoff

`claude --resume` on a session that has gone cold reloads the whole transcript without the prompt cache, so you pay for all of it again. This skill writes a short `HANDOFF.md` instead: where you stopped, what's done, what's next, open decisions, key files, and a one-line-per-session log at the bottom. The next session reads it and carries on.

### Hooks (recommended)

Two hooks make it automatic:

- **Stop** (`hooks/handoff_stop.py`): when Claude finishes a turn in which it edited files or ran commands, the hook blocks the stop and tells Claude to update `HANDOFF.md`. Turns that only answered questions stop normally. It runs on Stop because SessionEnd hooks can only run shell commands; they can't get the model to write anything. Stop fires after every turn, so the note stays current whenever you quit.
- **SessionStart** (`hooks/handoff_start.py`): loads `HANDOFF.md` into context when a session starts, after `/clear`, and after compaction.

Put this in **user settings** (`~/.claude/settings.json`) to get handoffs in every project. It matches the `-g` install path.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          { "type": "command", "command": "python3 \"$HOME/.claude/skills/session-handoff/hooks/handoff_start.py\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 \"$HOME/.claude/skills/session-handoff/hooks/handoff_stop.py\"" }
        ]
      }
    ]
  }
}
```

For one project only, install without `-g` and put [`hooks/settings.project.json`](session-handoff/hooks/settings.project.json) in that project's `.claude/settings.json`. It's the same block with paths under `$CLAUDE_PROJECT_DIR/.claude/skills/`. Commit it and your teammates get it too. If you already have hooks, add these entries to your existing `SessionStart` and `Stop` arrays.

Needs `python3`. No other dependencies. Test the hooks with `python3 session-handoff/hooks/test_hooks.py`.

### No hooks

Add one line to your `CLAUDE.md`:

```markdown
Read HANDOFF.md at the start; update it before ending.
```

Nothing enforces it, so the note only gets written when Claude remembers.

### Tested

Run on 2026-10-14 with Claude Code 2.1.300 and Sonnet 5.5, in an empty scratch repo with the project-scope hooks.

**Session 1.** Prompt: *"Build a tiny todo CLI in todo.py, storing todos in todos.json. The plan is four commands: add, list, done, delete. Do add and list now and try both once."*

Claude built `add` and `list`, ran them, and tried to stop. The Stop hook blocked it, and Claude wrote this note:

```markdown
# Handoff
Updated: 2026-10-14 16:14

## Where we stopped
Todo CLI in `todo.py` has `add` and `list` working and tested once. `done` and `delete` are not written yet.

## Done
- `todo.py` created: `add <text>` and `list` commands.
- Storage in `todos.json` beside the script; each todo is `{id, text, done}`.
- IDs are max+1, so deleting later won't reuse IDs.
- Ran `add "buy milk"` then `list`; both worked.

## Next
- Add `done <id>`: set `done` to true, report if the id is missing.
- Add `delete <id>`: remove the todo, report if the id is missing.
- Update the usage string in `main` to cover all four commands.
- Try each new command once.

## Open decisions / blockers
- `todos.json` still holds the "buy milk" test todo; remove it or keep it.
- None blocking.

## Key files
- `todo.py`: the CLI (`load`, `save`, `add`, `list_todos`, `main`).
- `todos.json`: data store, created on first `add`.

## Previous sessions
- 2026-10-14 (9584313d): Built todo.py with add and list, tested both once; done and delete still to do.
```

**Session 2.** New session, no `--resume`. Prompt: *"Keep going."*

The SessionStart hook loaded the note. Claude's first action was reading `todo.py`, then it added both commands and reported: *"`done <id>` and `delete <id>` now work in `todo.py`. I ran each once, and also with a missing id and a non-numeric id."* The Stop hook fired again and the log gained a line:

```markdown
## Previous sessions
- 2026-10-14 (04ce19e3): Added `done` and `delete` to todo.py, updated usage string, tested each once.
- 2026-10-14 (9584313d): Built todo.py with add and list, tested both once; done and delete still to do.
```

Session 1 cost $0.042 and session 2 cost $0.049, handoff included. After adding the excuse table and checklist to SKILL.md I ran both sessions again. The Stop hook blocked once per session, the SessionStart hook loaded the note, and session 2 built `done` and `delete` from "Keep going." alone ($0.040 and $0.071).

**Session 3, interactive.** Asked *"What did we do last time, and what's left?"* Claude answered from the note with no tool calls (*"Last time: We built todo.py, a small todo CLI. It now has four commands: add, list, done, and delete."*). Nothing changed that turn, so the Stop hook let it end and `HANDOFF.md` was left alone.

In headless `claude -p` runs the handoff is the last turn, so the printed result is Claude's reply after writing the note (it was "Done." in both runs above), not its summary of the work.

## Coming soon

<!-- Next skills go here. -->

## Other projects

- [Diagram Design](https://github.com/cathrynlavery/diagram-design): editorial diagrams for Claude Code and other agents.

## License

[MIT](LICENSE)
