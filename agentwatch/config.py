"""Configuration management for AgentWatch."""

import json
import shutil
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / "Projects" / "agentwatch"
CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
EXAMPLE_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.example.json"
LOGS_DIR = DEFAULT_CONFIG_DIR / "logs"
STATE_FILE = DEFAULT_CONFIG_DIR / "logs" / "state.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load configuration from config.json.  Exit with a clear message if missing."""
    target = Path(path) if path else CONFIG_FILE
    if not target.exists():
        print(f"[AgentWatch] Config file not found: {target}")
        print("[AgentWatch] Run 'agentwatch init' to create one.")
        raise SystemExit(1)
    try:
        with open(target, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[AgentWatch] Failed to parse config: {exc}")
        raise SystemExit(1)


def init_config() -> Path:
    """Copy config.example.json → config.json if the latter does not exist."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        print(f"[AgentWatch] {CONFIG_FILE} already exists — skipping init.")
        return CONFIG_FILE

    if not EXAMPLE_CONFIG_FILE.exists():
        print(f"[AgentWatch] {EXAMPLE_CONFIG_FILE} not found. Cannot initialise.")
        raise SystemExit(1)

    shutil.copy(EXAMPLE_CONFIG_FILE, CONFIG_FILE)
    print(f"[AgentWatch] Created {CONFIG_FILE}")
    print("[AgentWatch]   → Edit it and fill in your notifier.bark_key.")
    return CONFIG_FILE


def get_notifier_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract and validate notifier section."""
    nc = config.get("notifier", {})
    if nc.get("type") == "bark" and not nc.get("bark_key"):
        print("[AgentWatch] WARNING: bark_key is empty in config.json")
    return nc


def get_risk_policy(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("risk_policy", {})


def get_task_boundary(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("task_boundary", {})


def get_failure_policy(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("failure_policy", {})


def get_notification_rules(config: dict[str, Any]) -> dict[str, Any]:
    return config.get("notification_rules", {})
