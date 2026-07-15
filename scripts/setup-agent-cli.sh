#!/usr/bin/env bash
# Install and configure Cursor Agent CLI (local machine / CI).
# Secrets are NEVER written into the git repo.
#
# Usage:
#   export CURSOR_API_KEY='key_...'   # from https://cursor.com/dashboard/api
#   bash scripts/setup-agent-cli.sh
#
# Optional:
#   CURSOR_EMAIL='you@example.com' bash scripts/setup-agent-cli.sh

set -euo pipefail

echo "==> Installing Cursor Agent CLI"
curl https://cursor.com/install -fsS | bash

BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"

if ! grep -q 'HOME/.local/bin' "${HOME}/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
fi
export PATH="${BIN_DIR}:$PATH"

if ! command -v agent >/dev/null 2>&1; then
  echo "error: agent not found on PATH after install" >&2
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

if ! grep -q 'agent-auth.env' "${HOME}/.bashrc" 2>/dev/null; then
  cat >> "${HOME}/.bashrc" <<'EOF'

# Cursor Agent CLI auth (local secrets; never commit)
[ -f "$HOME/.cursor/agent-auth.env" ] && . "$HOME/.cursor/agent-auth.env"
EOF
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

# Load auth for this shell if present
if [[ -f "$AUTH_ENV" ]]; then
  # shellcheck disable=SC1090
  . "$AUTH_ENV"
fi

echo "==> Auth status:"
agent status || true

cat <<'EOF'

Done.

Quick start:
  source ~/.bashrc
  agent status
  agent -p "explain this repository"

If still not logged in:
  1) Create an API key at https://cursor.com/dashboard/api
  2) export CURSOR_API_KEY='...'
  3) Or run: NO_OPEN_BROWSER=1 agent login
EOF
