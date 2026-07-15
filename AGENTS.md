# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
The active product in this working tree is a **Clash / Clash Meta (mihomo) proxy configuration**
under `clash/` (`config.yaml`, `override.yaml`, `env.sh`, `README.md`). It is config/infra, not a
buildable app — it is loaded by an external `mihomo` binary. There is no package manager, no code
dependencies, and no database.

Note: the top-level `README.md` describes an unrelated Python ML project ("TimeCAP") and is stale
relative to this branch; ignore it when working on the `clash/` config. That code lives only on the
`origin/cursor/organize-finance-repo-6534` branch.

### Runtime
`mihomo` (Clash Meta) is the runtime and is preinstalled at `/usr/local/bin/mihomo`. Version pinned
during setup: `v1.19.28` (linux-amd64 `compatible` build). It is a system dependency (not a repo
dependency), so it is not reinstalled by the update script unless missing.

### Validate the config
```bash
mihomo -t -f clash/config.yaml -d /tmp/mihomo-test   # "test is successful" on success
```

### Run it (development)
```bash
mkdir -p /tmp/mihomo-run && cp clash/config.yaml /tmp/mihomo-run/config.yaml
mihomo -d /tmp/mihomo-run -f /tmp/mihomo-run/config.yaml
```
Listeners: HTTP proxy `7890`, SOCKS5 `7891`, control API `9090`, DNS `1053`.
First run downloads the GeoIP MMDB into the `-d` data dir (needs internet).

### Non-obvious caveats (important)
- **TProxy / Redir listeners fail** with `operation not permitted` in the container (they need
  `CAP_NET_ADMIN`/root). This is expected and harmless; HTTP/SOCKS/API still work.
- The config sets **both `port` and `mixed-port` to `7890`**, so mihomo logs
  `Start Mixed(http+socks) server error: ... address already in use`. Harmless — the plain HTTP
  proxy already owns `7890`.
- The `proxies:` in `config.yaml` are **placeholder example nodes** and cannot reach the internet.
  To exercise real traffic end-to-end, point the built-in selector at `DIRECT` via the control API:
  ```bash
  curl -X PUT http://127.0.0.1:9090/proxies/GLOBAL -d '{"name":"DIRECT"}'   # global mode uses GLOBAL group
  curl -x http://127.0.0.1:7890 https://api.ipify.org?format=json           # then proxy real traffic
  ```
- Switch modes at runtime without editing files:
  `curl -X PATCH http://127.0.0.1:9090/configs -d '{"mode":"rule"}'` (values: `global`/`rule`/`direct`).
- **No dashboard UI** is bundled (no `external-ui`), so `http://127.0.0.1:9090/ui` will 404. Use the
  REST API on `:9090` directly, or point an external Yacd/Dashboard at it.
- `source clash/env.sh` exports `http_proxy`/`https_proxy`/`all_proxy` for the current shell.
