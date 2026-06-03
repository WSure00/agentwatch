#!/usr/bin/env python3
"""Simulate a Claude Code hook event on stdin for testing hook processing.

Usage:
    python3 scripts/simulate_event.py danger   | agentwatch hook --event PreToolUse
    python3 scripts/simulate_event.py done     | agentwatch hook --event Stop
    python3 scripts/simulate_event.py drift    | agentwatch hook --event PreToolUse
    python3 scripts/simulate_event.py failure  | agentwatch hook --event PostToolUse
    python3 scripts/simulate_event.py permission | agentwatch hook --event Notification
"""

import json
import sys


SCENARIOS = {
    "danger": json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "git push origin main && rm -rf /tmp/build"},
        "working_dir": "/home/user/project",
    }),
    "done": json.dumps({
        "reason": "completed",
        "stop_reason": "task_finished",
    }),
    "drift": json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": "/home/user/project/train/model.py", "content": "..."},
        "working_dir": "/home/user/project",
    }),
    "failure": json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/"},
        "output": "3 failed, 0 passed, 1 error in 2.34s\nexit code: non-zero",
    }),
    "permission": json.dumps({
        "notification": {
            "title": "Permission Required",
            "message": "Claude needs your approval to run: rm -rf build/",
        },
    }),
    "approval-pending": json.dumps({
        "tool_use_id": "call_sim_approval_001",
        "tool_name": "Bash",
        "tool_input": {
            "command": "cd ~/Projects/agentwatch && git status",
            "description": "Check git status"
        },
        "working_dir": "/home/user/project",
    }),
    "auto-exec": json.dumps({
        "tool_use_id": "call_sim_autoexec_001",
        "tool_name": "Bash",
        "tool_input": {
            "command": "echo hello",
            "description": "Echo hello"
        },
        "working_dir": "/home/user/project",
    }),
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in SCENARIOS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(SCENARIOS.keys())}>", file=sys.stderr)
        sys.exit(1)
    print(SCENARIOS[sys.argv[1]])


if __name__ == "__main__":
    main()
