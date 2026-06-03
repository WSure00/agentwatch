#!/usr/bin/env python3
"""Standalone Bark push test — does not require the full agentwatch package.

Usage:
    python3 scripts/test_push.py [BARK_KEY]

If BARK_KEY is omitted, reads from agentwatch config.json.
"""

import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote


def main() -> None:
    bark_key = ""

    if len(sys.argv) > 1:
        bark_key = sys.argv[1]
    else:
        config_path = Path(__file__).resolve().parent.parent / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as fh:
                config = json.load(fh)
            bark_key = config.get("notifier", {}).get("bark_key", "")

    if not bark_key or bark_key == "YOUR_BARK_KEY":
        print("ERROR: bark_key not set. Provide it as argument or configure config.json")
        sys.exit(1)

    title = quote("AgentWatch 测试", safe="")
    body = quote("如果你在 Apple Watch 上看到这条消息，说明提醒链路已打通。", safe="")
    url = f"https://api.day.app/{bark_key}/{title}/{body}?group=AgentWatch&level=timeSensitive"

    print(f"Pushing to Bark (key: {bark_key[:4]}...{bark_key[-4:]})")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 200:
                print("SUCCESS: Notification sent. Check iPhone / Apple Watch.")
            else:
                print(f"Bark response: {data}")
    except Exception as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
