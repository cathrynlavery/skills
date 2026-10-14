#!/usr/bin/env python3
"""Tests for the session-handoff hooks. Run: python3 session-handoff/hooks/test_hooks.py"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STOP = os.path.join(HERE, "handoff_stop.py")
START = os.path.join(HERE, "handoff_start.py")


def run(script, payload, project):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env["CLAUDE_PROJECT_DIR"] = project
    out = subprocess.run(
        [sys.executable, script], input=json.dumps(payload),
        capture_output=True, text=True, env=env, check=True,
    ).stdout
    return json.loads(out) if out.strip() else None


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def transcript(path, tools, ts):
    """Write a transcript with one assistant entry per tool name at time ts."""
    with open(path, "w") as f:
        f.write(json.dumps({"type": "user", "timestamp": iso(ts - 1),
                            "message": {"content": "do the thing"}}) + "\n")
        for name in tools:
            f.write(json.dumps({"type": "assistant", "timestamp": iso(ts), "message": {
                "content": [{"type": "tool_use", "name": name, "input": {}}]}}) + "\n")


class StopHook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.log = os.path.join(self.dir, "t.jsonl")
        self.handoff = os.path.join(self.dir, "HANDOFF.md")

    def tearDown(self):
        self.tmp.cleanup()

    def stop(self, active=False):
        return run(STOP, {"session_id": "abcdef1234", "transcript_path": self.log,
                          "cwd": self.dir, "stop_hook_active": active}, self.dir)

    def test_read_only_turn_does_not_block(self):
        transcript(self.log, ["Read", "Grep"], time.time())
        self.assertIsNone(self.stop())

    def test_edit_with_no_handoff_blocks(self):
        transcript(self.log, ["Edit"], time.time())
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("HANDOFF.md", out["reason"])
        self.assertIn("(abcdef12)", out["reason"])

    def test_work_after_handoff_blocks(self):
        open(self.handoff, "w").write("# Handoff\n")
        os.utime(self.handoff, (time.time() - 600, time.time() - 600))
        transcript(self.log, ["Bash"], time.time())
        self.assertEqual(self.stop()["decision"], "block")

    def test_work_before_handoff_does_not_block(self):
        transcript(self.log, ["Write"], time.time() - 600)
        open(self.handoff, "w").write("# Handoff\n")
        self.assertIsNone(self.stop())

    def test_stop_hook_active_passes_through(self):
        transcript(self.log, ["Edit"], time.time())
        self.assertIsNone(self.stop(active=True))

    def test_missing_transcript_does_not_block(self):
        self.assertIsNone(self.stop())


class StartHook(unittest.TestCase):
    def test_no_handoff_loads_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(run(START, {"cwd": d, "source": "startup"}, d))

    def test_handoff_is_loaded(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "HANDOFF.md"), "w").write("## Next\n- ship it\n")
            out = run(START, {"cwd": d, "source": "startup"}, d)
            ctx = out["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertIn("- ship it", ctx)

    def test_long_handoff_is_truncated(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "HANDOFF.md"), "w").write("x" * 20000)
            ctx = run(START, {"cwd": d}, d)["hookSpecificOutput"]["additionalContext"]
            self.assertLess(len(ctx), 9000)
            self.assertIn("[truncated", ctx)


if __name__ == "__main__":
    unittest.main()
