# Cursor Agent CLI

在终端里安装、配置和排查 Cursor `agent` 命令。

## 一键安装（Linux / macOS）

```bash
export CURSOR_API_KEY='key_xxxxxxxx'   # 可选，来自 https://cursor.com/dashboard/api
bash scripts/setup-agent-cli.sh
```

或仅安装：

```bash
curl https://cursor.com/install -fsS | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc   # bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc    # zsh（macOS 常见）
source ~/.bashrc   # 或 source ~/.zshrc
agent --version
```

## Windows（原生 PowerShell）

**不要在 Git Bash 里运行 `curl | bash`**，会报 `Unsupported operating system: MINGW64`。

```powershell
irm 'https://cursor.com/install?win32=true' | iex
pwsh -File scripts/setup-agent-cli.ps1
```

然后**新开一个 PowerShell / Windows Terminal 窗口**：

```powershell
agent --version
agent status
```

### Windows：禁止运行脚本（PSSecurityException）

如果报错类似：

```text
无法加载文件 ...\cursor-agent\agent.ps1，因为在此系统上禁止运行脚本
```

**推荐修复**（只对当前用户生效，安全）：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

输入 `Y` 确认后，再运行：

```powershell
agent --version
agent status
```

**临时绕过**（不改系统策略）：

```powershell
& "$env:LOCALAPPDATA\cursor-agent\agent.cmd" --version
& "$env:LOCALAPPDATA\cursor-agent\agent.cmd" status
```

## 桌面终端跑不了？（常见原因）

| 现象 | 原因 | 解决办法 |
|------|------|----------|
| `agent: command not found` | PATH 未生效 | 新开终端；或 `source ~/.bashrc` / `source ~/.zshrc` |
| 只有 bash 配了 PATH，你用 zsh | 旧脚本只写了 `.bashrc` | 运行 `bash scripts/setup-agent-cli.sh`（会同时配置 bash/zsh/profile） |
| 安装成功但当前窗口找不到 | 环境变量未加载 | `export PATH="$HOME/.local/bin:$PATH"` |
| Windows Git Bash 安装失败 | Unix 安装脚本不支持 MINGW | 改用 **PowerShell** 安装（见上） |
| Windows `PSSecurityException` | PowerShell 执行策略禁止 `.ps1` | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `agent status` 未登录 | 缺少 API Key | 见下方「认证」 |
| 网络/代理问题 | 无法连接 Cursor 服务 | 配置代理或检查防火墙 |

### 自动诊断

```bash
bash scripts/doctor-agent-cli.sh
```

会检查：二进制是否存在、PATH、shell 配置文件、登录状态，并给出中文修复建议。

## 认证

| 方式 | 适用场景 |
|------|----------|
| `CURSOR_API_KEY` | 脚本、CI、无浏览器环境 |
| `agent login` | 本机浏览器登录 |

```bash
# API Key（推荐）
export CURSOR_API_KEY='key_xxxxxxxx'
bash scripts/setup-agent-cli.sh
agent status

# 浏览器登录
NO_OPEN_BROWSER=1 agent login   # 打印 URL，在浏览器完成
agent status
```

密钥只保存在 `~/.cursor/agent-auth.env`（权限 600），**不要提交到 git**。

## 常用命令

```bash
agent status
agent about
agent models
agent -p "总结这个仓库"
agent --mode ask "训练流程是怎样的？"
agent update
```

## 代理（可选，本地 Clash / mihomo）

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export all_proxy=socks5://127.0.0.1:7891
```

## 参考

- 安装：https://cursor.com/docs/cli/installation
- 认证：https://cursor.com/docs/cli/authentication
- API Key：https://cursor.com/dashboard/api
