#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Open AgentWatch App.command — double-click to launch the menu bar app.
#
# If build/AgentWatch.app doesn't exist, prompts you to build it first.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$SCRIPT_DIR/build/AgentWatch.app"

if [ -d "$APP_PATH" ]; then
    echo "Launching AgentWatch menu bar app ..."
    open "$APP_PATH"
    echo ""
    echo "Look for '● AW' in your menu bar (top-right of the screen)."
    echo "Click the icon to open the AgentWatch menu."
    echo ""
    read -r -p "Press Enter to exit this window (app stays running)..."
else
    echo "============================================"
    echo "  AgentWatch.app not found"
    echo "============================================"
    echo ""
    echo "Please build the app first:"
    echo ""
    echo "  cd ~/Projects/agentwatch"
    echo "  bash macos/build_app.sh"
    echo ""
    read -r -p "Press Enter to exit..."
fi
