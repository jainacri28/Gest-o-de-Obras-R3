$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
$appFile = Join-Path $projectRoot "app.py"

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

if (-not (Test-Path $venvPython)) {
    Write-Host "Python da virtualenv não encontrado em: $venvPython" -ForegroundColor Red
    Write-Host "Crie ou repare a venv antes de iniciar o app." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $appFile)) {
    Write-Host "Arquivo app.py não encontrado em: $appFile" -ForegroundColor Red
    exit 1
}

Write-Host "Abrindo aplicativo de Gestão de Obras..." -ForegroundColor Cyan
Write-Host "URL esperada: http://localhost:8501" -ForegroundColor DarkCyan

& $venvPython -m streamlit run $appFile
