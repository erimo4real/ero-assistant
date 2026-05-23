$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found. Creating .venv..."
    $created = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $projectRoot ".venv")
        $created = $LASTEXITCODE -eq 0
    }
    if (-not $created -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -m venv (Join-Path $projectRoot ".venv")
        $created = $LASTEXITCODE -eq 0
    }
    if (-not $created) {
        throw "Could not find Python. Install Python 3, then run this again."
    }
    & $python -m pip install -r (Join-Path $projectRoot "requirements.txt")
}

& $python (Join-Path $projectRoot "personal_assistant.py")
