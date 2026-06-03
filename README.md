# AgentWatch

**Apple Watch notifications for Claude Code and AI agent workflows.**

AgentWatch lets you walk away from your Mac (or Windows PC) while Claude Code works. When the agent needs your approval, needs attention, or finishes a task — your Apple Watch vibrates with a short event card. No more babysitting the terminal.

> AgentWatch 让你不用一直盯着 Claude Code。只有当 Agent 需要授权、需要你处理或任务完成时，它才通过 Apple Watch 震动和简短卡片提醒你。

## Why AgentWatch?

Claude Code is powerful — but you don't want to watch every command. You only need to know when:
- A real "Allow this bash command?" permission dialog appears
- The agent needs your approval or input
- A task finishes and needs your review

AgentWatch hooks into Claude Code's event system, filters out the noise, and pushes only truly actionable alerts to your wrist.

## Features

- **Apple Watch / iPhone notifications** via [Bark](https://apps.apple.com/app/bark/id1403753865) (free, open source)
- **PermissionRequest hook** support — the reliable signal for real "Allow" dialogs
- **PermissionDenied hook** logging — track when you deny operations
- **Actionable notification mode** — only pushes when user interaction is genuinely needed
- **Stop hook** task completion reminders
- **PreToolUse timeout log-only** by default — avoids false alerts from long commands
- **Persona Themes** — 总裁版, 少爷版, 大小姐版, 皇上版, 甄嬛版
- **macOS menu bar app** — native Swift + AppKit
- **Windows tray app** — native C# / .NET 8 WinForms
- **Task boundary + silent drift/risk logging**
- **Zero extra Python dependencies** — standard library only
- **Local-first** — no extra LLM required, no analytics, no cloud beyond Bark

## How It Works

```
Claude Code hooks           AgentWatch Python CLI
─────────────────         ─────────────────────────
PreToolUse         ──▶     danger / drift detection
PostToolUse        ──▶     failure counting
Notification      ──▶     attention classification
Stop              ──▶     task completion
PermissionRequest ──▶     ✓ PUSH to Watch (reliable)
PermissionDenied  ──▶     log only (no push)
                           │
                           ├── notification policy (actionable by default)
                           ├── persona message builder
                           ├── Bark push ──▶ iPhone ──▶ Apple Watch
                           └── logs/agentwatch_events.jsonl
```

**Key design:**
- `PermissionRequest` is the **reliable** signal for real "Allow this command?" prompts
- `Notification` is the fallback for general attention events
- `Stop` handles task completion
- `PreToolUse` timeout defaults to **log-only** — slow builds ≠ permission prompts

## System Requirements

| Platform | Requirements |
|----------|-------------|
| macOS | Python 3.10+, Xcode Command Line Tools (for menu bar app), Bash, Claude Code |
| Windows | Python 3.10+, .NET 8 SDK (for tray app), PowerShell, Claude Code |
| iOS | [Bark](https://apps.apple.com/app/bark/id1403753865) (free) |
| Watch | Apple Watch paired to iPhone (recommended) |

## Quick Start: macOS

```bash
git clone https://github.com/YOUR_NAME/agentwatch.git ~/Projects/agentwatch
cd ~/Projects/agentwatch

# Setup Python
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Configure
agentwatch init
agentwatch config bark        # paste your Bark URL or key
agentwatch config test        # verify notifications work

# Install hooks (manual, opt-in)
bash install_claude_hooks.sh

# Build & launch menu bar app
bash macos/build_app.sh
open build/AgentWatch.app
```

The app lives in your **menu bar** (no Dock icon). Look for `● AW` in the top-right.
You can also double-click `AgentWatch.command` for everyday use, or `AgentWatch Setup.command` for first-time setup.

## Quick Start: Windows

```powershell
cd %USERPROFILE%\Projects
git clone https://github.com/YOUR_NAME/agentwatch.git
cd agentwatch

# Setup
powershell -ExecutionPolicy Bypass -File windows\setup_windows.ps1

# Configure
.\.venv\Scripts\agentwatch.exe config bark
.\.venv\Scripts\agentwatch.exe config test

# Install hooks
powershell -ExecutionPolicy Bypass -File windows\install_claude_hooks_windows.ps1

# Build & launch
powershell -ExecutionPolicy Bypass -File windows\build_app.ps1
build\windows\AgentWatchTray\AgentWatchTray.exe
```

Or double-click `Open AgentWatch Windows App.bat`.

## Bark Setup

AgentWatch sends notifications through [Bark](https://apps.apple.com/app/bark/id1403753865), a free open-source iOS push app.

1. Install Bark on your iPhone
2. Open Bark → the URL shows your key: `https://api.day.app/YOUR_KEY/`
3. Configure in AgentWatch:

**CLI:**
```bash
agentwatch config bark        # paste full URL or bare key
agentwatch config show        # view config (key redacted)
agentwatch config test        # send test notification
```

**macOS menu bar:** `● AW` → `Add / Update Bark Key...`

**Windows tray:** Right-click → `Add / Update Bark Key...`

## Claude Code Hooks

Hooks are **manual, opt-in** — AgentWatch never modifies your Claude Code configuration automatically.

Six hooks are registered: `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `PermissionRequest`, `PermissionDenied`.

**macOS:**
```bash
bash install_claude_hooks.sh     # install
bash uninstall_claude_hooks.sh   # remove
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File windows\install_claude_hooks_windows.ps1
powershell -ExecutionPolicy Bypass -File windows\uninstall_claude_hooks_windows.ps1
```

> **Upgrade note:** If you installed hooks before v0.8.0, re-run the install script to add `PermissionRequest` / `PermissionDenied`. Run `agentwatch doctor` to verify — it should show `Claude hooks: Installed` (6/6).

## Notification Policy

AgentWatch uses **actionable mode** by default — only truly interactive events push to your watch.

### Pushed to Watch

| Event | Signal |
|-------|--------|
| Real "Allow this command?" dialog | **PermissionRequest** hook |
| Agent needs attention / input | Notification hook (fallback) |
| Task completed | Stop hook |

### Logged Only (no watch push)

| Event | Signal |
|-------|--------|
| Operation denied by user | PermissionDenied hook |
| Tool call still open (uncertain) | PreToolUse timeout (log-only) |
| Dangerous operation detected | PreToolUse danger keywords |
| Task boundary drift | PreToolUse forbidden paths |
| Consecutive failures | PostToolUse error count |

To push PreToolUse timeouts (accepts false-positive risk from slow commands):
```json
"approval_detection": { "timeout_watch_notify": true }
```

## Persona Themes

Switch notification style without restarting. Six themes available:

| Theme | Key | Style |
|-------|-----|-------|
| Off | `off` | Default AgentWatch text |
| 总裁版 | `boss` | Dramatic CEO alerts |
| 少爷版 | `heir_male` | Estate manager reports |
| 大小姐版 | `heir_female` | Estate manager reports |
| 皇上版 | `emperor` | Imperial court style |
| 甄嬛版 | `palace` | Palace intrigue style |

**CLI:**
```bash
agentwatch persona show
agentwatch persona set boss
agentwatch persona set emperor
agentwatch persona off
agentwatch persona test permission    # preview, no push
```

**macOS:** `● AW` → `Persona Theme` → choose theme

**Windows:** Right-click tray icon → `Persona Theme` → choose theme

Personas only change notification **wording** — the notification **policy** is unchanged.

## macOS Menu Bar App

```bash
bash macos/build_app.sh          # build (requires Swift)
open build/AgentWatch.app        # launch
# or double-click: Open AgentWatch App.command
```

The app runs in your menu bar (no Dock icon). Features:
- Bark configuration & test push
- Persona theme switching
- Recent events with source labels
- Hook status & approval timeout status
- Task boundary management
- Quick access to logs, config, README

## Windows Tray App

```powershell
powershell -ExecutionPolicy Bypass -File windows\build_app.ps1   # build (requires .NET 8)
build\windows\AgentWatchTray\AgentWatchTray.exe                  # launch
# or double-click: Open AgentWatch Windows App.bat
```

Right-click the tray icon for full access to status, events, persona switching, and actions.

## Common Commands

| Command | Description |
|---------|-------------|
| `agentwatch doctor` | Health check |
| `agentwatch monitor` | Live ANSI dashboard (Ctrl+C to exit) |
| `agentwatch start` | Doctor + monitor |
| `agentwatch config bark` | Set Bark key |
| `agentwatch config show` | Show Bark config (key redacted) |
| `agentwatch config test` | Send test notification |
| `agentwatch persona show` | Show current persona |
| `agentwatch persona set <theme>` | Switch persona theme |
| `agentwatch persona off` | Disable persona |
| `agentwatch persona test <event>` | Preview persona text |
| `agentwatch simulate permission-request` | Simulate Allow dialog |
| `agentwatch simulate permission-denied` | Simulate deny |
| `agentwatch simulate done` | Simulate task complete |
| `agentwatch simulate approval-pending` | Simulate tool timeout |
| `agentwatch task quick` | Interactive task boundary |
| `agentwatch task clear` | Clear task boundary |
| `agentwatch logs --tail 20` | View recent events |

## Testing

Quick verification after setup:

```bash
agentwatch simulate permission-request    # should push to Watch (persona applied)
agentwatch simulate done                  # should push "task done"
agentwatch simulate approval-pending      # should LOG only (no push)
agentwatch simulate permission-denied     # should LOG only (no push)
```

## Troubleshooting

### Apple Watch not vibrating
- Confirm Bark is installed and working on your iPhone
- Run `agentwatch config test`
- Check iPhone Settings → Notifications → Bark
- On Apple Watch: Watch app → Notifications → mirror Bark

### Bark returns "device token not found"
- Your Bark key is incorrect. Open the Bark iOS app and copy the current key.
- Ensure `bark_server` is `https://api.day.app`

### "Allow this bash command?" but Watch didn't vibrate
- Run `agentwatch doctor`
- If it says `Missing PermissionRequest`, reinstall hooks:
  - macOS: `bash install_claude_hooks.sh`
  - Windows: `powershell -File windows\install_claude_hooks_windows.ps1`
- Test: `agentwatch simulate permission-request`
- Restart Claude Code session for new hooks to take effect

### Too many false alerts from long Bash commands
- This is the default behavior — PreToolUse timeouts are log-only
- Verify `approval_detection.timeout_watch_notify` is `false`

### macOS app double-click has no window
- It's a menu bar app — look for `● AW` in the top-right

### Windows tray app doesn't start
- Ensure .NET 8 SDK is installed: `dotnet --version`
- Rebuild: `powershell -File windows\build_app.ps1`

## Privacy & Security

- `config.json` is **gitignored** — your Bark key stays local
- `logs/` and `diagnostics/` are **gitignored** — may contain command summaries
- AgentWatch does **not** send code contents to any third-party LLM or API
- Bark notifications transmit only the notification title and body to your configured Bark server
- You can self-host Bark — set `bark_server` in `config.json`
- See [SECURITY.md](SECURITY.md) for details

## Roadmap

- [ ] GitHub Release binaries (`.app`, `.exe`)
- [ ] Away mode — auto-detect when you leave
- [ ] Session summary notifications
- [ ] Guard mode — auto-block dangerous operations
- [ ] More persona themes
- [ ] Pushover / ntfy notification support
- [ ] Native iOS / watchOS actions

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
