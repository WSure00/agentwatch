# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

AgentWatch monitors Claude Code (and other AI agents) and pushes status to an iPhone / Apple Watch via [Bark](https://github.com/Finb/Bark). Claude Code fires lifecycle **hooks**; each hook invokes the `agentwatch` CLI, which classifies the event, evaluates risk/policy, builds a Chinese-language notification, and pushes it via Bark — so a user away from their desk learns when the agent needs approval, finished, or did something dangerous.

The notification message text and persona themes are in **Chinese** by design — match that when editing `message_builder.py` / `persona.py`.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                      # installs the `agentwatch` console script
agentwatch init                       # copy config.example.json -> config.json, create logs/

# Configure & verify
agentwatch config bark --value <KEY>  # or interactive: agentwatch config bark
agentwatch config test                # send a Bark test push (alias: agentwatch test-push)
agentwatch doctor                     # health check: python, config, bark key, hooks, last event

# Wire up Claude Code hooks (edits ~/.claude/settings.json, backs it up first)
bash install_claude_hooks.sh
bash uninstall_claude_hooks.sh

# Run / observe
agentwatch start                      # doctor + live monitor dashboard
agentwatch monitor                    # live ANSI dashboard (Ctrl+C to exit)
agentwatch logs --tail 20             # dump recent JSONL events

# Test event handling WITHOUT a real Claude session — primary dev/debug loop
agentwatch simulate danger            # also: done, drift, failure, permission,
                                      #       permission-request, permission-denied,
                                      #       approval-pending, auto-exec
agentwatch simulate danger --notify   # force a push even when policy would stay silent
```

There is **no test suite, linter, or build step for the Python package** — `pip install -e .` plus `agentwatch simulate ...` is the verification loop. `scripts/simulate_event.py` and `scripts/test_push.py` are standalone helpers.

Native desktop apps build separately: `bash macos/build_app.sh` (Swift Package Manager) and `windows/build_app.ps1` (.NET 8 SDK). These are thin status-bar/tray wrappers that shell out to the same `agentwatch` CLI — the Python core is the source of truth.

**Linux** has no native GUI app by design — it uses the cross-platform terminal monitor (`agentwatch start`/`monitor`) plus a local desktop-notification backend (`desktop.py` → `notify-send`). The `linux/` dir holds shell launchers only: `setup.sh` (venv + install + init + doctor), `agentwatch-monitor.sh` (the launcher), `agentwatch.desktop` + `install_desktop_entry.sh` (an app-menu entry; the `__PROJECT_DIR__` placeholder in the `.desktop` is substituted at install time). Hook installation reuses the existing cross-platform `install_claude_hooks.sh` — no Linux-specific hook script.

## Architecture

A hook fires → `cli.cmd_hook(event_name)` reads JSON from stdin and runs a fixed pipeline:

```
read_stdin_json → parse_event → classify → policy evaluation → build_message → should_send_notification → send_bark + append_event
```

Module responsibilities (all under `agentwatch/`):

- **`cli.py`** — entry point (`agentwatch` script / `python -m agentwatch.cli`). Owns `cmd_hook` (the pipeline above) plus all user subcommands. **Invariant: `cmd_hook` must never exit non-zero** — a crashing hook would block Claude Code, so everything is wrapped and it always `raise SystemExit(0)`.
- **`event_parser.py`** — `parse_event` flattens the raw hook JSON into `{tool_name, tool_input, raw_text, has_error, ...}`. `raw_text` is *all strings concatenated* for keyword scanning. Tool identity (`tool_use_id`) is extracted here for matching Pre/PostToolUse pairs.
- **`classifier.py`** — maps a parsed event to an event-type string (`pretooluse`, `posttooluse`, `posttooluse_error`, `permission_required`, `attention_required`, `task_done`, `permission_denied`, `info`). Notification-hook text is scanned for permission vs. attention keywords (EN + ZH sets).
- **`policy.py`** — risk evaluation: `evaluate_danger` (keyword/path/extension matching, with word-boundary regex to avoid false positives like "rm" in "permissions"), `evaluate_drift` (task-boundary violations), `evaluate_failure` (consecutive-failure counter). These can *upgrade* an `info`/`pretooluse` classification to `danger`/`drift`/`failure`. Also owns `should_send_notification` — the routing gate.
- **`message_builder.py`** — turns an event type + policy info into `{title, body}`. `TITLE_MAP` holds the canonical titles; then `apply_persona` overlays the theme.
- **`persona.py`** — optional flavor themes (`boss`, `heir_male`, `heir_female`, `emperor`, `palace`) that rewrite title/body per event type. Falls through to the default message if a theme lacks a template for that event type.
- **`notifier.py`** — `send_bark` builds the Bark URL and GETs it. `notify(title, body, config)` is the **dispatch entry point** the CLI now calls everywhere: it fans out to Bark (`config["notifier"]`) **and** the local desktop backend (`config["desktop_notify"]`), returning `True` if any backend succeeded. All return `bool`; **callers must not crash on `False`**.
- **`desktop.py`** — `send_desktop` pops a local desktop notification via `notify-send` (Linux). Probes with `shutil.which`; if `notify-send` is absent (macOS/Windows/headless) or `desktop_notify.enabled` is false, it silently returns `False`. Best-effort, never raises — same contract as `send_bark`.
- **`store.py`** — JSONL event log + `state.json`. Append-only events log auto-**redacts the bark_key** before writing. Holds the failure counter and the pending-actions store (see approval detection).
- **`config.py`** — `config.json` lives at the **project root**, auto-detected by walking up to `pyproject.toml` (then `$AGENTWATCH_HOME`, cwd, legacy `~/Projects/agentwatch`). No hardcoded home paths. `config.json` is gitignored (holds the bark_key).

### Two control flows that aren't obvious from one file

**Notification policy (the silent-vs-push gate).** `should_send_notification` is the single decision point. In the default `actionable` mode, only `task_done` and `permission_required`/`attention_required` push to the Watch; `danger`/`drift`/`failure` are evaluated and **logged but NOT pushed** (they show in the monitor/logs only). `verbose` mode pushes everything non-`info`. So "danger detected but no Watch notification" is by design, not a bug — check the mode. `--notify` on `simulate` bypasses this gate for testing.

**Approval detection (the delayed background checker).** Claude Code has no "waiting for your approval" hook. AgentWatch infers it: on `PreToolUse` for a candidate tool (Bash/Edit/Write/…), it registers a pending action in `pending_actions.json` and **spawns a detached subprocess** (`agentwatch pending-check --id ... --delay N`, default 4s). If the matching `PostToolUse` arrives within the delay, the pending action is cleared (the agent auto-executed — no notification). If it's still pending after the delay, the tool is presumed blocked on user approval. By default this is *log-only* (`possible_permission_wait`); set `approval_detection.timeout_watch_notify: true` to actually push. The Pre/Post match uses `tool_use_id` first, falling back to most-recent-pending by `tool_name`. Simulate this with `agentwatch simulate approval-pending` / `auto-exec`.

### Claude Code hook integration

`install_claude_hooks.sh` merges six hooks into `~/.claude/settings.json` using the matcher-group schema (`hooks.<Event>[].hooks[].command`), each calling `<python> -m agentwatch.cli hook --event <Event>`. Events: `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `PermissionRequest`, `PermissionDenied`. The script is idempotent (strips prior agentwatch entries, including a legacy flat format, before re-adding) and backs up settings.json first. `doctor` reports `Installed` only when all six are present.

## Conventions

- New event types must be threaded through all of: `classifier.py` (produce it) → `policy.py` `should_send_notification` (route it) → `message_builder.TITLE_MAP` + a `_body_*` helper (render it) → `persona.py` templates (optional flavor). Missing any link yields a generic fallback message.
- The events log is the audit trail; every handled path calls `append_event`. Don't write secrets into log entries — `store._redact` only knows about the bark_key.
- Risk levels are the Chinese strings `极高 / 高 / 中 / 低`; suggestions and bodies are Chinese.
