"""Send local desktop notifications via `notify-send` (Linux).

This is a best-effort, side-channel backend that runs alongside Bark so that a
user sitting at a Linux machine sees the same alert on their desktop without
needing their phone.  It is intentionally tolerant:

  * If `notify-send` is not installed (e.g. macOS / Windows / headless), it
    silently returns False.
  * Any failure is swallowed and returns False.

Like `notifier.send_bark`, the caller MUST NOT crash on False — hooks always
exit 0.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any


def _urgency_for(urgency: str) -> str:
    """Validate the urgency string; fall back to 'normal'."""
    return urgency if urgency in ("low", "normal", "critical") else "normal"


def send_desktop(title: str, body: str, desktop_config: dict[str, Any]) -> bool:
    """Pop a local desktop notification through `notify-send`.

    Returns True on success, False on any failure (including when desktop
    notifications are disabled or `notify-send` is unavailable).
    """
    if not desktop_config.get("enabled", False):
        return False

    notify_send = shutil.which("notify-send")
    if not notify_send:
        # Not a Linux desktop (or notify-send not installed) — silently skip.
        return False

    urgency = _urgency_for(desktop_config.get("urgency", "normal"))
    expire_ms = desktop_config.get("expire_ms", 8000)
    icon = desktop_config.get("icon", "dialog-information")
    app_name = desktop_config.get("app_name", "AgentWatch")

    cmd = [
        notify_send,
        "-a", app_name,
        "-u", urgency,
        "-t", str(expire_ms),
        "-i", icon,
        title,
        body,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return result.returncode == 0
    except Exception as exc:  # noqa: BLE001 — best-effort, never crash a hook.
        print(f"[AgentWatch] Desktop notify failed: {exc}", flush=True)
        return False
