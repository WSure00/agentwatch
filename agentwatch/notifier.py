"""Send notifications via Bark (push to iPhone / Apple Watch)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from agentwatch.desktop import send_desktop
from agentwatch.presence import PresenceState, get_presence_state
from agentwatch.utils import url_encode


def notify(
    title: str,
    body: str,
    config: dict[str, Any],
    *,
    event_type: str | None = None,
    presence_override: str | None = None,
) -> bool:
    """Dispatch a notification across all configured backends.

    Reads the full *config* and fans out to:
      * Bark (Apple Watch / iPhone)  — config["notifier"]
      * Local desktop notification    — config["desktop_notify"]

    When *event_type* is provided and focus_detection is enabled, the
    presence-aware router decides which backends to use:
      * AWAY              → Bark + desktop
      * PRESENT_UNFOCUSED → desktop only (Bark if danger)
      * PRESENT_FOCUSED   → silent (desktop if permission/danger)

    When *event_type* is None (test pushes, config test), both backends
    fire unconditionally.

    *presence_override* forces a specific presence state (``"away"``,
    ``"present_unfocused"``, ``"present_focused"``) instead of detecting it.
    Used by ``agentwatch simulate --presence``.

    Returns True if *any* backend reported success.
    Never raises — callers (hooks) must stay exit-0.
    """
    notifier_config = config.get("notifier", {}) or {}
    desktop_config = config.get("desktop_notify", {}) or {}

    # Presence-aware routing.
    route = _route_backends(event_type, config, presence_override)

    # If presence routing silenced everything, note it and return True
    # (intentional silence is not a failure).
    if not route["bark"] and not route["desktop"]:
        print(f"[AgentWatch] Presence routing: silent ({event_type})", flush=True)
        return True

    bark_ok = False
    if route["bark"]:
        try:
            bark_ok = send_bark(title, body, notifier_config)
        except Exception as exc:  # noqa: BLE001 — never crash a hook.
            print(f"[AgentWatch] Bark dispatch error: {exc}", flush=True)

    desktop_ok = False
    if route["desktop"]:
        try:
            desktop_ok = send_desktop(title, body, desktop_config)
        except Exception as exc:  # noqa: BLE001 — never crash a hook.
            print(f"[AgentWatch] Desktop dispatch error: {exc}", flush=True)

    return bark_ok or desktop_ok


def _route_backends(
    event_type: str | None,
    config: dict[str, Any],
    presence_override: str | None = None,
) -> dict[str, bool]:
    """Decide which notification backends to use based on presence state.

    Returns ``{"bark": bool, "desktop": bool}``.

    When *event_type* is None (test/config-test pushes), both backends fire.
    When focus_detection is disabled in config, both backends fire (original behaviour).
    When *presence_override* is set, use that state instead of real detection.
    """
    # No event_type → bypass presence routing (test pushes).
    if event_type is None:
        return {"bark": True, "desktop": True}

    focus_config = config.get("focus_detection", {}) or {}
    if not focus_config.get("enabled", True):
        return {"bark": True, "desktop": True}

    # Determine presence state — override or real detection.
    if presence_override:
        try:
            presence = PresenceState(presence_override)
        except ValueError:
            # Invalid override — fall back to real detection.
            presence = get_presence_state(focus_config)
    else:
        try:
            presence = get_presence_state(focus_config)
        except Exception:
            # Detection crashed — be conservative: push everywhere.
            return {"bark": True, "desktop": True}

    always_bark_danger = focus_config.get("always_bark_on_danger", True)

    # Is this a high-priority event that should always reach the user?
    is_critical = event_type in ("permission_required", "attention_required")
    is_danger = event_type == "danger"

    if presence == PresenceState.AWAY:
        # User is gone — push everywhere.
        return {"bark": True, "desktop": True}

    if presence == PresenceState.PRESENT_UNFOCUSED:
        # User is at machine but not looking at our terminal.
        # Desktop always; Bark only for critical/danger events.
        bark = is_critical or (is_danger and always_bark_danger)
        return {"bark": bark, "desktop": True}

    if presence == PresenceState.PRESENT_FOCUSED:
        # User is staring at the terminal — mostly silent.
        # Critical events still get a local nudge; danger gets desktop too.
        if is_critical:
            return {"bark": False, "desktop": True}
        if is_danger:
            return {"bark": always_bark_danger, "desktop": True}
        # task_done, info, etc. → fully silent.
        return {"bark": False, "desktop": False}

    # Unknown state — be conservative.
    return {"bark": True, "desktop": True}


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
