#!/usr/bin/env bash
# Install and configure Cursor Agent CLI for desktop terminals.
# Fixes the common "agent: command not found" issue when only ~/.bashrc was updated
# but the desktop terminal uses zsh or a login shell that reads ~/.profile instead.
#
# Usage:
#   export CURSOR_API_KEY='key_...'   # from https://cursor.com/dashboard/api
#   bash scripts/setup-agent-cli.sh
#
# Windows (native): use PowerShell instead:
#   irm 'https://cursor.com/install?win32=true' | iex
#   pwsh -File scripts/setup-agent-cli.ps1

set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
AUTH_SOURCE='[ -f "$HOME/.cursor/agent-auth.env" ] && . "$HOME/.cursor/agent-auth.env"'

append_once() {
  local file="$1"
  local marker="$2"
  local block="$3"
  [[ -f "$file" ]] || touch "$file"
  if ! grep -qF "$marker" "$file" 2>/dev/null; then
    printf '\n%s\n' "$block" >> "$file"
    echo "  + updated ${file}"
  else
    echo "  = already configured ${file}"
  fi
}

configure_path() {
  echo "==> Configuring PATH for desktop shells"
  local block
  block="# Cursor Agent CLI
${PATH_LINE}
${AUTH_SOURCE}"

  append_once "${HOME}/.bashrc" 'HOME/.local/bin' "$block"
  append_once "${HOME}/.zshrc" 'HOME/.local/bin' "$block"
  # Login shells (some desktop terminals) read ~/.profile instead of ~/.bashrc
  append_once "${HOME}/.profile" 'HOME/.local/bin' "$block"

  if [[ -d "${HOME}/.config/fish" ]]; then
    local fish_conf="${HOME}/.config/fish/conf.d/cursor-agent.fish"
    mkdir -p "$(dirname "$fish_conf")"
    cat > "$fish_conf" <<'EOF'
# Cursor Agent CLI
fish_add_path "$HOME/.local/bin"
if test -f "$HOME/.cursor/agent-auth.env"
    source "$HOME/.cursor/agent-auth.env"
end
EOF
    echo "  + wrote ${fish_conf}"
  fi

  export PATH="${BIN_DIR}:$PATH"
}

echo "==> Installing Cursor Agent CLI"
if ! curl https://cursor.com/install -fsS | bash; then
  echo "error: install failed. On native Windows use PowerShell:" >&2
  echo "  irm 'https://cursor.com/install?win32=true' | iex" >&2
  exit 1
fi

mkdir -p "$BIN_DIR"
configure_path

if ! command -v agent >/dev/null 2>&1; then
  echo "error: agent not found after install. Expected: ${BIN_DIR}/agent" >&2
  echo "Try: export PATH=\"\$HOME/.local/bin:\$PATH\" && agent --version" >&2
  exit 1
fi

echo "==> agent version: $(agent --version)"

mkdir -p "${HOME}/.cursor"
chmod 700 "${HOME}/.cursor"

AUTH_ENV="${HOME}/.cursor/agent-auth.env"
umask 077

if [[ -n "${CURSOR_API_KEY:-}" ]]; then
  {
    echo "export CURSOR_API_KEY='${CURSOR_API_KEY}'"
    if [[ -n "${CURSOR_EMAIL:-}" ]]; then
      echo "export CURSOR_EMAIL='${CURSOR_EMAIL}'"
    fi
  } > "$AUTH_ENV"
  chmod 600 "$AUTH_ENV"
  echo "==> Wrote ${AUTH_ENV} (mode 600)"
else
  echo "==> CURSOR_API_KEY not set; writing template to ${AUTH_ENV}.example"
  cat > "${HOME}/.cursor/agent-auth.env.example" <<'EOF'
# Copy to ~/.cursor/agent-auth.env and fill in values.
# Get an API key: https://cursor.com/dashboard/api
export CURSOR_API_KEY='key_xxxxxxxx'
# export CURSOR_EMAIL='you@example.com'
EOF
  chmod 600 "${HOME}/.cursor/agent-auth.env.example"
fi

if [[ ! -f "${HOME}/.cursor/cli-config.json" ]]; then
  cat > "${HOME}/.cursor/cli-config.json" <<'EOF'
{
  "version": 1,
  "editor": { "vimMode": false },
  "permissions": { "allow": [], "deny": [] },
  "network": { "useHttp1ForAgent": false }
}
EOF
  chmod 600 "${HOME}/.cursor/cli-config.json"
  echo "==> Created ~/.cursor/cli-config.json"
fi

if [[ -f "$AUTH_ENV" ]]; then
  # shellcheck disable=SC1090
  . "$AUTH_ENV"
fi

echo "==> Auth status:"
agent status || true

cat <<'EOF'

Done.

Desktop terminal — pick the command for YOUR shell, then verify:

  # bash (Ubuntu default terminal)
  source ~/.bashrc
  agent --version

  # zsh (macOS / many Linux desktops)
  source ~/.zshrc
  agent --version

  # if still "command not found", open a NEW terminal window

Still broken? Run the diagnostic:
  bash scripts/doctor-agent-cli.sh

Auth (if agent status says not logged in):
  1) Create an API key at https://cursor.com/dashboard/api
  2) export CURSOR_API_KEY='key_...' && bash scripts/setup-agent-cli.sh
  3) Or: NO_OPEN_BROWSER=1 agent login
EOF
