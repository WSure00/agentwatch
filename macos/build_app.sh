#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# AgentWatch — build the macOS menu bar .app bundle
#
# Prerequisites: Xcode or Xcode Command Line Tools (swift build)
#
# Usage:
#   bash macos/build_app.sh
#
# Output:
#   build/AgentWatch.app
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SWIFT_PROJECT="$SCRIPT_DIR/AgentWatchMenuBar"
BUILD_DIR="$PROJECT_DIR/build"
APP_NAME="AgentWatch"
APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"

echo "============================================"
echo "  AgentWatch — Building Menu Bar App"
echo "============================================"
echo ""

# --- 1. Swift build ---
echo "[1/5] Building Swift executable (release) ..."
cd "$SWIFT_PROJECT"
swift build -c release --disable-sandbox 2>&1
echo "      Done."

# Find the built binary
SWIFT_BIN=$(find "$SWIFT_PROJECT/.build" -path "*/release/AgentWatchMenuBar" -type f 2>/dev/null | head -1)
if [ -z "$SWIFT_BIN" ]; then
    echo "ERROR: Could not find built binary."
    exit 1
fi
echo "      Binary: $SWIFT_BIN"

# --- 2. Create .app bundle structure ---
echo "[2/5] Creating .app bundle structure ..."
rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
echo "      $APP_BUNDLE"

# --- 3. Copy executable ---
echo "[3/5] Copying executable ..."
cp "$SWIFT_BIN" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
echo "      Done."

# --- 4. Write Info.plist ---
echo "[4/5] Writing Info.plist ..."
cat > "$APP_BUNDLE/Contents/Info.plist" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>AgentWatch</string>
    <key>CFBundleDisplayName</key>
    <string>AgentWatch</string>
    <key>CFBundleIdentifier</key>
    <string>com.agentwatch.menubar</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>AgentWatch</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST_EOF
echo "      Done."

# --- 5. Verify ---
echo "[5/5] Verifying bundle ..."
echo "      $(ls -la "$APP_BUNDLE/Contents/MacOS/$APP_NAME")"
echo "      LSUIElement: $(/usr/libexec/PlistBuddy -c 'Print :LSUIElement' "$APP_BUNDLE/Contents/Info.plist" 2>/dev/null || echo 'true')"

echo ""
echo "============================================"
echo "  Build Complete"
echo "============================================"
echo ""
echo "  App:  $APP_BUNDLE"
echo ""
echo "  To launch:"
echo "    open '$APP_BUNDLE'"
echo "    or double-click 'Open AgentWatch App.command'"
echo ""
echo "  The app runs in the menu bar (no Dock icon)."
echo "  Look for '● AW' in the top-right of your screen."
echo ""
