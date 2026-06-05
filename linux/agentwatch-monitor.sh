#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# AgentWatch — launch the monitoring panel on Linux.
#
# For first-time setup, run linux/setup.sh instead.
#
# Usage:
#   bash linux/agentwatch-monitor.sh
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "============================================"
    echo "  AgentWatch — Virtual environment not found"
    echo "============================================"
    echo ""
    echo "Please run setup first:"
    echo ""
    echo "  bash \"$PROJECT_DIR/linux/setup.sh\""
    echo ""
    read -r -p "Press Enter to exit..."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
agentwatch start
read -r -p "Press Enter to exit..."
