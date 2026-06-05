# AgentWatch TODO

## Features

### [ ] Focus/Presence-Aware Notifications

根据用户是否在机器前，智能路由通知：

1. **锁屏 / 不在机器前** → 推送 Bark（手机 + Apple Watch）
2. **在机器前，但焦点不在终端** → 只发本地 `notify-send`，不推手机
3. **在机器前，且焦点在 Claude Code 终端** → 任务完成通知静默，只保留高危 / 需要审批的推送

**涉及模块：**
- 新建 `agentwatch/presence.py`：检测 idle（`xprintidle`）、锁屏（D-Bus `org.freedesktop.login1`）、焦点窗口（`xdotool`）
- 修改 `agentwatch/notifier.py`：按三层逻辑路由
- 修改 `agentwatch/policy.py`：焦点在终端时对 `task_done` 降级静默
- 修改 `config.json`：新增 `focus_detection` 配置节

**实现前待确认：**
- 机器是 X11 还是 Wayland？
- 终端窗口标题关键词（如 `claude`、`tmux`、`kitty`）
