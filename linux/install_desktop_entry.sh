#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# AgentWatch — install a desktop menu entry on Linux.
#
# Copies agentwatch.desktop into ~/.local/share/applications/ with the project
# path injected, and marks the launcher scripts executable.  After this you can
# launch AgentWatch from your application menu (GNOME/KDE/etc.).
#
# Usage:
#   bash linux/install_desktop_entry.sh
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

APPS_DIR="$HOME/.local/share/applications"
DEST="$APPS_DIR/agentwatch.desktop"
TEMPLATE="$SCRIPT_DIR/agentwatch.desktop"

if [ ! -f "$TEMPLATE" ]; then
    echo "[AgentWatch] ERROR: template not found: $TEMPLATE"
    exit 1
fi

mkdir -p "$APPS_DIR"

# Make launcher scripts executable.
chmod +x "$SCRIPT_DIR/agentwatch-monitor.sh" "$SCRIPT_DIR/setup.sh" 2>/dev/null || true

# Inject the real project path into the .desktop template.
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$TEMPLATE" > "$DEST"
chmod +x "$DEST" 2>/dev/null || true

# Refresh the desktop database if the tool is available (best-effort).
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo "[AgentWatch] Desktop entry installed: $DEST"
echo "[AgentWatch] Look for 'AgentWatch' in your application menu."
echo "[AgentWatch] To remove it:  rm \"$DEST\""
