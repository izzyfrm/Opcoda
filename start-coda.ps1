# Starts Coda's model API and the private Cloudflare Tunnel that connects it to opcoda.cc.
# Run from PowerShell:  .\start-coda.ps1      (Ctrl+C stops both)
# By default, serve the local Ollama coding model. Use -Backend coda for the from-scratch model.
# To pin a Coda checkpoint: .\start-coda.ps1 -Checkpoint checkpoints\coda-v4-best.pt
param(
    [string]$Checkpoint = "",
    [ValidateSet("ollama", "coda")][string]$Backend = "ollama",
    [string]$OllamaModel = "qwen2.5-coder:3b"
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".coda-model-token")) { throw "Missing .coda-model-token. See web/README.md, 'Deploy'." }
if (-not (Test-Path "tunnel/opcoda-model.yml")) { throw "Missing tunnel/opcoda-model.yml. See web/README.md, 'Deploy'." }

if ($Checkpoint) { $env:CODA_CHECKPOINT = $Checkpoint; $Backend = "coda" }
else { Remove-Item Env:CODA_CHECKPOINT -ErrorAction SilentlyContinue }
$env:CODA_BACKEND = $Backend
$env:CODA_OLLAMA_MODEL = $OllamaModel
if ($Backend -eq "ollama") {
    $installed = & ollama list
    if ($LASTEXITCODE -ne 0 -or -not ($installed | Select-String -SimpleMatch $OllamaModel)) {
        throw "Ollama model $OllamaModel is unavailable. Run: ollama pull $OllamaModel"
    }
}
$tunnel = Start-Process cloudflared -ArgumentList "tunnel", "--config", "tunnel/opcoda-model.yml", "run" -PassThru -WindowStyle Hidden
try {
    & .\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
}
finally {
    if (-not $tunnel.HasExited) { Stop-Process -Id $tunnel.Id }
}
