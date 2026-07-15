# Cursor Agent CLI

Install and authenticate the `agent` CLI for terminal / CI use.

## One-shot setup

```bash
# Preferred: API key from https://cursor.com/dashboard/api
export CURSOR_API_KEY='key_xxxxxxxx'
export CURSOR_EMAIL='you@example.com'   # optional
bash scripts/setup-agent-cli.sh
```

Or install only:

```bash
curl https://cursor.com/install -fsS | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
agent --version
```

## Authentication

| Method | When to use |
|--------|-------------|
| `CURSOR_API_KEY` | Scripts, CI, cloud agents |
| `agent login` | Interactive browser login |

```bash
# API key
export CURSOR_API_KEY='key_xxxxxxxx'
agent status

# Browser login (prints URL if NO_OPEN_BROWSER=1)
NO_OPEN_BROWSER=1 agent login
agent status
```

Secrets are stored only in `~/.cursor/agent-auth.env` (mode `600`). **Do not commit API keys or passwords.**

## Common commands

```bash
agent status
agent about
agent models
agent -p "summarize this repo"
agent --mode ask "how does training work?"
agent update
```

## Notes

- Invalid / short keys are rejected; dashboard keys usually look like `key_...`.
- If login shows Cloudflare “Verify you are human”, finish the flow in your own browser with the printed URL, or use an API key instead.
- Proxy (optional, if using Clash locally):

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7891
```
