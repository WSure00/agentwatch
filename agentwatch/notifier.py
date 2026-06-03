"""Send notifications via Bark (push to iPhone / Apple Watch)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from agentwatch.utils import url_encode


def send_bark(title: str, body: str, notifier_config: dict[str, Any]) -> bool:
    """Push a notification through the Bark API.

    Returns True on success, False on failure.
    The caller MUST NOT crash on False — hooks always exit 0.
    """
    bark_key = notifier_config.get("bark_key", "")
    if not bark_key or bark_key == "YOUR_BARK_KEY":
        print("[AgentWatch] WARN: bark_key is not configured. Skipping push.")
        return False

    bark_server = notifier_config.get("bark_server", "https://api.day.app").rstrip("/")
    group = notifier_config.get("group", "AgentWatch")
    level = notifier_config.get("level", "timeSensitive")

    # Build the Bark URL.
    encoded_title = url_encode(title)
    encoded_body = url_encode(body)
    url = (
        f"{bark_server}/{bark_key}/{encoded_title}/{encoded_body}"
        f"?group={url_encode(group)}&level={url_encode(level)}"
    )

    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 200:
                return True
            else:
                print(f"[AgentWatch] Bark API returned: {data}", flush=True)
                return False
    except urllib.error.HTTPError as exc:
        body_text = ""
        try:
            body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        print(f"[AgentWatch] Bark push failed (HTTP {exc.code}): {body_text or exc.reason}", flush=True)
        return False
    except Exception as exc:
        print(f"[AgentWatch] Bark push failed: {exc}", flush=True)
        return False
