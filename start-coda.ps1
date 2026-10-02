# Starts Coda's model API and the private Cloudflare Tunnel that connects it to opcoda.cc.
# Run from PowerShell:  .\start-coda.ps1      (Ctrl+C stops both)
# By default server.py serves the newest model (coda-v4 if trained, otherwise Phase 3).
# To pin one:  .\start-coda.ps1 -Checkpoint checkpoints\coda-v4-best.pt
param([string]$Checkpoint = "")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".coda-model-token")) { throw "Missing .coda-model-token. See web/README.md, 'Deploy'." }
if (-not (Test-Path "tunnel/opcoda-model.yml")) { throw "Missing tunnel/opcoda-model.yml. See web/README.md, 'Deploy'." }

if ($Checkpoint) { $env:CODA_CHECKPOINT = $Checkpoint } else { Remove-Item Env:CODA_CHECKPOINT -ErrorAction SilentlyContinue }
$tunnel = Start-Process cloudflared -ArgumentList "tunnel", "--config", "tunnel/opcoda-model.yml", "run" -PassThru -NoNewWindow
try {
    & .\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
}
finally {
    if (-not $tunnel.HasExited) { Stop-Process -Id $tunnel.Id }
}
