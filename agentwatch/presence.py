"""Focus / presence detection — determines how to route notifications.

Three-state model:
  AWAY              — user is idle or screen is locked  → push everywhere
  PRESENT_UNFOCUSED — user is at machine but looking at another window → desktop only
  PRESENT_FOCUSED   — user is staring at the Claude Code terminal → mostly silent

Detection strategies degrade gracefully:
  X11 + xprintidle + xdotool  → full detection
  X11 without xprintidle      → skip idle, use lock + focus
  Wayland / headless          → conservative fallback (PRESENT_UNFOCUSED)
  Everything fails            → presence routing disabled (original behavior)

All subprocess calls use timeout=2s to never block a hook.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from enum import Enum
from typing import Any


class PresenceState(Enum):
    """User presence state relative to the Claude Code terminal."""

    AWAY = "away"
    PRESENT_UNFOCUSED = "present_unfocused"
    PRESENT_FOCUSED = "present_focused"


# ── Public API ───────────────────────────────────────────────────────────


def get_presence_state(focus_config: dict[str, Any]) -> PresenceState:
    """Detect the current user presence state.

    *focus_config* is the ``focus_detection`` section from config.json.
    If ``enabled`` is False, returns AWAY (which causes full notification —
    the safest default when presence routing is disabled but still called).

    Never raises — all detection failures are caught and degraded.
    """
    if not focus_config.get("enabled", True):
        return PresenceState.AWAY

    try:
        # Step 1: Lock screen check (fastest — single loginctl call).
        if _is_screen_locked():
            return PresenceState.AWAY

        # Step 2: Idle time check.
        threshold_ms = focus_config.get("idle_threshold_seconds", 60) * 1000
        idle_result = _check_idle(threshold_ms)
        if idle_result == "idle":
            return PresenceState.AWAY

        # Step 3: Focus window check (only if user is active).
        focus_result = _check_focus()
        if focus_result == "focused":
            return PresenceState.PRESENT_FOCUSED

        # Default: user is present but not focused on our terminal.
        return PresenceState.PRESENT_UNFOCUSED

    except Exception:
        # Ultimate fallback — assume away so notifications still reach the user.
        return PresenceState.AWAY


# ── Lock screen detection ────────────────────────────────────────────────


def _is_screen_locked() -> bool:
    """Check whether the screen is currently locked.

    Returns True if locked, False if not locked, and False on detection failure
    (conservative: don't falsely claim locked).
    """
    # Strategy 1: loginctl (systemd — works on most Linux desktops).
    locked = _check_loginctl_locked()
    if locked is not None:
        return locked

    # Strategy 2: D-Bus GNOME ScreenSaver.
    locked = _check_dbus_screensaver()
    if locked is not None:
        return locked

    # No lock detection available — assume not locked.
    return False


def _check_loginctl_locked() -> bool | None:
    """Use loginctl to check LockedHint. Returns None if unavailable."""
    if not shutil.which("loginctl"):
        return None

    try:
        # Find the current user's session.
        result = subprocess.run(
            ["loginctl", "list-sessions", "--no-legend"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None

        uid = str(os.getuid())
        session_id = None
        for line in result.stdout.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 3 and parts[1] == uid:
                session_id = parts[0]
                break

        if not session_id:
            return None

        # Query LockedHint for this session.
        result = subprocess.run(
            ["loginctl", "show-session", session_id, "-p", "LockedHint"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None

        return "LockedHint=yes" in result.stdout

    except (subprocess.TimeoutExpired, OSError):
        return None


def _check_dbus_screensaver() -> bool | None:
    """Use D-Bus to check GNOME ScreenSaver. Returns None if unavailable."""
    if not shutil.which("dbus-send"):
        return None

    try:
        result = subprocess.run(
            [
                "dbus-send",
                "--session",
                "--dest=org.gnome.ScreenSaver",
                "--type=method_call",
                "--print-reply",
                "/org/gnome/ScreenSaver",
                "org.gnome.ScreenSaver.GetActive",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None

        return "boolean true" in result.stdout

    except (subprocess.TimeoutExpired, OSError):
        return None


# ── Idle detection ───────────────────────────────────────────────────────


def _check_idle(threshold_ms: int) -> str | None:
    """Check whether the user is idle.

    Returns "idle" if idle time exceeds *threshold_ms*, "active" if below,
    or None if detection is unavailable.
    """
    # Strategy 1: xprintidle (X11 standard).
    idle_ms = _get_xprintidle_ms()
    if idle_ms is not None:
        return "idle" if idle_ms > threshold_ms else "active"

    # Strategy 2: D-Bus Mutter IdleMonitor (GNOME Wayland).
    idle_ms = _get_dbus_idle_ms()
    if idle_ms is not None:
        return "idle" if idle_ms > threshold_ms else "active"

    # No idle detection available — assume active (conservative: don't skip notifications).
    return None


def _get_xprintidle_ms() -> int | None:
    """Get idle time in ms via xprintidle. Returns None if unavailable."""
    if not shutil.which("xprintidle"):
        return None

    try:
        result = subprocess.run(
            ["xprintidle"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None
        return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def _get_dbus_idle_ms() -> int | None:
    """Get idle time via D-Bus Mutter IdleMonitor. Returns None if unavailable."""
    if not shutil.which("dbus-send"):
        return None

    try:
        result = subprocess.run(
            [
                "dbus-send",
                "--session",
                "--dest=org.gnome.Mutter.IdleMonitor",
                "--type=method_call",
                "--print-reply",
                "/org/gnome/Mutter/IdleMonitor/Core",
                "org.gnome.Mutter.IdleMonitor.GetIdletime",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None

        # Parse "uint64 12345" from the reply.
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("uint64"):
                return int(line.split()[1])

        return None

    except (subprocess.TimeoutExpired, OSError, ValueError, IndexError):
        return None


# ── Focus window detection ───────────────────────────────────────────────


def _check_focus() -> str | None:
    """Check whether the focused window is our terminal.

    Returns "focused" if our terminal has focus, "unfocused" if another window
    has focus, or None if detection is unavailable.
    """
    # Strategy 1: xdotool + WINDOWID (X11 standard).
    focus = _check_xdotool_focus()
    if focus is not None:
        return focus

    # Strategy 2: xdotool PID-based lookup (if WINDOWID is not set).
    focus = _check_xdotool_pid()
    if focus is not None:
        return focus

    # No focus detection available.
    return None


def _check_xdotool_focus() -> str | None:
    """Compare xdotool active window with $WINDOWID. Returns None if unavailable."""
    if not shutil.which("xdotool"):
        return None

    window_id = os.environ.get("WINDOWID")
    if not window_id:
        return None

    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None

        active_window = result.stdout.strip()

        # xdotool returns decimal, WINDOWID may be decimal or hex (0x...).
        try:
            active_dec = int(active_window)
        except ValueError:
            return None

        try:
            our_dec = int(window_id, 0)  # auto-detect base (0x prefix → hex)
        except ValueError:
            return None

        return "focused" if active_dec == our_dec else "unfocused"

    except (subprocess.TimeoutExpired, OSError):
        return None


def _check_xdotool_pid() -> str | None:
    """Use xdotool to find windows belonging to our process tree. Returns None if unavailable."""
    if not shutil.which("xdotool"):
        return None

    # Only use this fallback when WINDOWID is not set.
    if os.environ.get("WINDOWID"):
        return None

    try:
        # Get the active window's PID.
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowpid"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return None

        active_pid = int(result.stdout.strip())

        # Walk up the process tree to see if the active window's PID is
        # an ancestor (or descendant) of our own process.
        our_pid = os.getpid()
        if _is_pid_related(active_pid, our_pid):
            return "focused"

        return "unfocused"

    except (subprocess.TimeoutExpired, OSError, ValueError):
        return None


def _is_pid_related(active_pid: int, our_pid: int) -> bool:
    """Check whether *active_pid* and *our_pid* share a process ancestry.

    Walks both PIDs up to PID 1 via /proc/*/stat to see if they share a
    common ancestor (e.g. both are children of the same terminal emulator).
    """
    ancestors_a = _get_pid_ancestors(active_pid)
    ancestors_b = _get_pid_ancestors(our_pid)

    # If they share any ancestor (other than init/systemd), they're related.
    common = ancestors_a & ancestors_b
    common.discard(1)  # discard PID 1 (init/systemd)
    return bool(common)


def _get_pid_ancestors(pid: int) -> set[int]:
    """Return the set of ancestor PIDs for *pid* (including itself)."""
    ancestors: set[int] = set()
    current = pid
    for _ in range(50):  # safety limit
        ancestors.add(current)
        if current <= 1:
            break
        try:
            stat_path = f"/proc/{current}/stat"
            with open(stat_path) as f:
                # Format: "pid (comm) state ppid ..."
                # The comm field can contain spaces/parens, so split from the right.
                parts = f.read().rsplit(")", 1)
                if len(parts) < 2:
                    break
                fields = parts[1].strip().split()
                if len(fields) < 2:
                    break
                ppid = int(fields[1])  # ppid is the 4th field (index 1 after split)
                current = ppid
        except (OSError, ValueError, IndexError):
            break
    return ancestors
