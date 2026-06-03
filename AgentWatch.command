#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# AgentWatch.command — double-click to launch the AgentWatch monitoring panel.
#
# For first-time setup, use AgentWatch Setup.command instead.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "============================================"
    echo "  AgentWatch — Virtual environment not found"
    echo "============================================"
    echo ""
    echo "Please run setup first:"
    echo ""
    echo "  cd ~/Projects/agentwatch"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -e ."
    echo ""
    echo "Or double-click AgentWatch Setup.command"
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
agentwatch start
read -r -p "Press Enter to exit..."
