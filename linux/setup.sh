#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# AgentWatch — first-time setup on Linux.
#
# Creates .venv, installs agentwatch, runs `agentwatch init`, then `doctor`.
# Does NOT auto-install Claude Code hooks (run install_claude_hooks.sh for that).
#
# Usage:
#   bash linux/setup.sh
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "============================================"
echo "  AgentWatch — First-Time Setup (Linux)"
echo "============================================"
echo ""

# --- python check ---
PYTHON_BIN="$(command -v python3 || command -v python || echo '')"
if [ -z "$PYTHON_BIN" ]; then
    echo "[AgentWatch] ERROR: python3 not found. Install Python 3.10+ and retry."
    exit 1
fi

# --- .venv ---
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment ..."
    "$PYTHON_BIN" -m venv .venv
    echo "      .venv created."
else
    echo "[1/4] Virtual environment already exists — skipping."
fi

# --- pip install ---
echo "[2/4] Installing agentwatch ..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip setuptools 2>/dev/null || true
pip install -q -e .
echo "      Done."

# --- agentwatch init ---
echo "[3/4] Initialising config and logs ..."
agentwatch init
echo ""

# --- agentwatch doctor ---
echo "[4/4] Running health check ..."
agentwatch doctor || true

# --- optional dependency hint ---
if ! command -v notify-send >/dev/null 2>&1; then
    echo ""
    echo "[AgentWatch] Note: 'notify-send' not found — local desktop notifications"
    echo "             will be skipped. To enable them, install libnotify, e.g.:"
    echo "               Debian/Ubuntu:  sudo apt install libnotify-bin"
    echo "               Fedora:         sudo dnf install libnotify"
    echo "               Arch:           sudo pacman -S libnotify"
fi

# --- presence detection tools ---
MISSING_PRESENCE=""
command -v xprintidle >/dev/null 2>&1 || MISSING_PRESENCE="${MISSING_PRESENCE}xprintidle "
command -v xdotool    >/dev/null 2>&1 || MISSING_PRESENCE="${MISSING_PRESENCE}xdotool "
if [ -n "$MISSING_PRESENCE" ]; then
    echo ""
    echo "[AgentWatch] Note: presence detection tools not found: ${MISSING_PRESENCE}"
    echo "             These enable smart notification routing (idle/lock/focus)."
    echo "             Without them, notifications use conservative fallbacks."
    echo "             Install (optional):"
    echo "               Debian/Ubuntu:  sudo apt install xprintidle xdotool"
fi

# --- next steps ---
echo ""
echo "============================================"
echo "  Next Steps"
echo "============================================"
echo ""
echo "  1. Configure your Bark key (for Apple Watch / iPhone):"
echo "       agentwatch config bark"
echo "     (Local desktop notifications work without Bark.)"
echo ""
echo "  2. Test notifications:"
echo "       agentwatch config test"
echo ""
echo "  3. Install Claude Code hooks (recommended):"
echo "       bash \"$PROJECT_DIR/install_claude_hooks.sh\""
echo ""
echo "  4. Launch the monitor:"
echo "       bash \"$PROJECT_DIR/linux/agentwatch-monitor.sh\""
echo "     or, for a desktop menu entry:"
echo "       bash \"$PROJECT_DIR/linux/install_desktop_entry.sh\""
echo ""
