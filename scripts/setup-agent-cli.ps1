# Install and configure Cursor Agent CLI on native Windows (PowerShell).
# Do NOT use "curl | bash" in Git Bash — it fails on MINGW64.
#
# Usage (PowerShell):
#   irm 'https://cursor.com/install?win32=true' | iex
#   pwsh -File scripts/setup-agent-cli.ps1
#
# Optional:
#   $env:CURSOR_API_KEY = 'key_...'
#   pwsh -File scripts/setup-agent-cli.ps1

$ErrorActionPreference = 'Stop'

function Ensure-AgentExecutionPolicy {
    $policy = Get-ExecutionPolicy -Scope CurrentUser
    if ($policy -in @('Restricted', 'AllSigned', 'Undefined')) {
        Write-Host '==> PowerShell blocks .ps1 scripts; setting CurrentUser to RemoteSigned' -ForegroundColor Yellow
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    }
}

function Invoke-Agent {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    $cmd = Join-Path $env:LOCALAPPDATA 'cursor-agent\agent.cmd'
    if (Test-Path $cmd) {
        & $cmd @Args
        return
    }
    & agent @Args
}

Write-Host '==> Installing Cursor Agent CLI (Windows native)' -ForegroundColor Cyan
irm 'https://cursor.com/install?win32=true' | iex

$agentCmd = Get-Command agent -ErrorAction SilentlyContinue
if (-not $agentCmd) {
    $fallback = Join-Path $env:LOCALAPPDATA 'cursor-agent\agent.cmd'
    if (Test-Path $fallback) {
        $dir = Split-Path $fallback -Parent
        $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        if ($userPath -notlike "*$dir*") {
            [Environment]::SetEnvironmentVariable('Path', "$dir;$userPath", 'User')
            $env:Path = "$dir;$env:Path"
            Write-Host "  + added $dir to user PATH"
        }
    } else {
        Write-Error "agent not found after install. Expected under $env:LOCALAPPDATA\cursor-agent\"
    }
}

Ensure-AgentExecutionPolicy

Write-Host "==> agent version: $(Invoke-Agent --version)"

$cursorDir = Join-Path $env:USERPROFILE '.cursor'
New-Item -ItemType Directory -Force -Path $cursorDir | Out-Null

$authEnv = Join-Path $cursorDir 'agent-auth.env'
if ($env:CURSOR_API_KEY) {
    @(
        "export CURSOR_API_KEY='$($env:CURSOR_API_KEY)'"
        if ($env:CURSOR_EMAIL) { "export CURSOR_EMAIL='$($env:CURSOR_EMAIL)'" }
    ) | Where-Object { $_ } | Set-Content -Encoding UTF8 $authEnv
    Write-Host "==> Wrote $authEnv"
} else {
    @'
# Copy to ~/.cursor/agent-auth.env and fill in values.
# Get an API key: https://cursor.com/dashboard/api
export CURSOR_API_KEY='key_xxxxxxxx'
'@ | Set-Content -Encoding UTF8 (Join-Path $cursorDir 'agent-auth.env.example')
    Write-Host '==> Wrote agent-auth.env.example (set CURSOR_API_KEY and re-run to save auth)'
}

Write-Host '==> Auth status:'
Invoke-Agent status

Write-Host @'

Done.

Open a NEW PowerShell or Windows Terminal window, then run:
  agent --version
  agent status

If you see PSSecurityException / 禁止运行脚本:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  # or use: & "$env:LOCALAPPDATA\cursor-agent\agent.cmd" --version

If Git Bash says "Unsupported operating system: MINGW64", use PowerShell instead.
'@
