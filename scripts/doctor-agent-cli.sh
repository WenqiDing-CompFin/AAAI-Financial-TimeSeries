#!/usr/bin/env bash
# Diagnose why `agent` does not work in a desktop terminal.
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
AGENT_PATH="${BIN_DIR}/agent"
WIN_AGENT="${LOCALAPPDATA:-}/cursor-agent/agent.cmd"

ok() { echo "  [OK] $*"; }
warn() { echo "  [!!] $*"; }
fail() { echo "  [FAIL] $*"; }

echo "==> Cursor Agent CLI doctor"
echo "Shell: ${SHELL:-unknown}  |  User: $(whoami)  |  OS: $(uname -s 2>/dev/null || echo Windows)"

echo ""
echo "-- Binary --"
if command -v agent >/dev/null 2>&1; then
  ok "agent on PATH: $(command -v agent)"
  agent --version 2>/dev/null && ok "agent --version works" || warn "agent found but --version failed"
elif [[ -x "$AGENT_PATH" ]]; then
  fail "agent exists at $AGENT_PATH but NOT on PATH"
  echo "       Fix: export PATH=\"\$HOME/.local/bin:\$PATH\""
elif [[ -f "$WIN_AGENT" ]]; then
  fail "Windows agent at $WIN_AGENT but not on PATH — use PowerShell, not Git Bash"
  echo "       Fix: open PowerShell and run: agent --version"
else
  fail "agent not installed"
  echo "       Fix (Linux/macOS): bash scripts/setup-agent-cli.sh"
  echo "       Fix (Windows):     irm 'https://cursor.com/install?win32=true' | iex"
fi

echo ""
echo "-- PATH --"
case ":$PATH:" in
  *":${BIN_DIR}:"*) ok "~/.local/bin is in PATH" ;;
  *) fail "~/.local/bin missing from PATH";;
esac

echo ""
echo "-- Shell config --"
for f in .bashrc .zshrc .profile; do
  if [[ -f "${HOME}/${f}" ]] && grep -q 'HOME/.local/bin' "${HOME}/${f}" 2>/dev/null; then
    ok "${f} contains PATH entry"
  else
    warn "${f} has no Cursor PATH entry (may be OK if you use another shell)"
  fi
done

echo ""
echo "-- Auth --"
if [[ -f "${HOME}/.cursor/agent-auth.env" ]]; then
  ok "~/.cursor/agent-auth.env exists"
else
  warn "no ~/.cursor/agent-auth.env — run agent login or set CURSOR_API_KEY"
fi

if command -v agent >/dev/null 2>&1; then
  echo ""
  echo "-- agent status --"
  agent status || warn "not authenticated (see docs/agent-cli.md)"
fi

echo ""
echo "==> Quick fixes (桌面终端常见修复)"
cat <<'EOF'
1) 关闭终端，重新打开一个新窗口（必须新开，source 只对当前窗口生效）
2) bash 用户:  source ~/.bashrc
   zsh 用户:   source ~/.zshrc
3) 仍找不到命令:  export PATH="$HOME/.local/bin:$PATH"
4) Windows 不要用 Git Bash 安装，请用 PowerShell:
     irm 'https://cursor.com/install?win32=true' | iex
5) 登录失败: 到 https://cursor.com/dashboard/api 创建 API Key
     export CURSOR_API_KEY='key_...'
     bash scripts/setup-agent-cli.sh
EOF
