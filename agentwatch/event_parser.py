"""Parse Claude Code hook JSON into a structured internal event."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agentwatch.utils import flatten_strings


def parse_event(raw: dict[str, Any] | None, event_name: str) -> dict[str, Any]:
    """Turn a raw Claude Code hook payload into an AgentWatch internal event dict.

    Parameters
    ----------
    raw : dict or None
        The JSON parsed from stdin.  May be None when stdin was empty.
    event_name : str
        One of PreToolUse, PostToolUse, Notification, Stop.

    Returns
    -------
    dict with keys:
        timestamp, event_name, raw_text, tool_name, tool_input,
        has_error, parsed, raw_event
    """
    parsed = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_name": event_name,
        "raw_text": "",
        "tool_name": "",
        "tool_input": {},
        "has_error": False,
        "parsed": True,
        "raw_event": raw or {},
    }

    if raw is None:
        return parsed

    # Flatten all strings for keyword matching.
    all_strings = flatten_strings(raw)
    parsed["raw_text"] = " ".join(all_strings)

    # Extract tool_name / tool_input for PreToolUse / PostToolUse.
    tool_name = raw.get("tool_name", "") or raw.get("tool", "") or ""
    if not tool_name and isinstance(raw.get("tool_use"), dict):
        tool_name = raw["tool_use"].get("name", "")
    parsed["tool_name"] = tool_name

    tool_input = raw.get("tool_input", {}) or raw.get("input", {})
    if isinstance(tool_input, str):
        try:
            import json as _json
            tool_input = _json.loads(tool_input)
        except Exception:
            tool_input = {"raw": tool_input}
    parsed["tool_input"] = tool_input if isinstance(tool_input, dict) else {}

    # Detect error indicators for PostToolUse.
    error_keywords = {"error", "failed", "exception", "traceback", "non-zero", "exit code", "traceback", "stack trace"}
    raw_lower = parsed["raw_text"].lower()
    if any(kw in raw_lower for kw in error_keywords):
        parsed["has_error"] = True

    return parsed


def extract_tool_identity(parsed: dict[str, Any]) -> str:
    """Extract a stable tool-call identity from a parsed event.

    Prefers tool_use_id from raw_event, falls back to empty string.
    """
    raw = parsed.get("raw_event", {}) or {}
    tuid = raw.get("tool_use_id", "") or ""
    if not tuid and isinstance(raw.get("tool_use"), dict):
        tuid = raw["tool_use"].get("id", "") or ""
    return tuid


def extract_tool_summary(parsed: dict[str, Any]) -> str:
    """Produce a short human-readable summary of the tool call."""
    tool_name = parsed.get("tool_name", "") or "Unknown"
    tool_input = parsed.get("tool_input", {}) or {}

    command = tool_input.get("command", "")
    file_path = tool_input.get("file_path", "")
    url = tool_input.get("url", "")
    notebook_path = tool_input.get("notebook_path", "")

    snippet = command or file_path or url or notebook_path or ""
    if snippet:
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        return f"{tool_name}: {snippet}"

    for k in ("command", "file_path", "content", "url", "description"):
        v = tool_input.get(k, "")
        if v and isinstance(v, str) and len(v) > 2:
            short = v[:120] + "..." if len(v) > 120 else v
            return f"{tool_name}: {short}"

    return f"{tool_name}"


def make_pending_action_id(parsed: dict[str, Any]) -> str:
    """Create a pending-action id, preferring tool_use_id from the hook JSON."""
    tuid = extract_tool_identity(parsed)
    if tuid:
        return tuid
    from agentwatch.store import new_action_id
    return new_action_id()
