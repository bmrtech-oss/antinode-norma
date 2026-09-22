$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot '.runtime'
$pidFile = Join-Path $runtimeDir 'backend.pid'
$logFile = Join-Path $runtimeDir 'backend.log'
$errorLogFile = Join-Path $runtimeDir 'backend.error.log'

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path $pidFile) {
    $existingPid = [int](Get-Content $pidFile -Raw).Trim()
    $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if ($existingProcess) {
        Write-Output "Backend is already running (PID $existingPid)."
        exit 0
    }
    Remove-Item $pidFile -Force
}

$pythonPath = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonPath)) {
    $pythonPath = 'python'
}

$process = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList '-m', 'uvicorn', 'antinode_norma.server.api:app', '--host', '0.0.0.0', '--port', '8000' `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errorLogFile `
    -PassThru

$process.Id | Set-Content $pidFile
Write-Output "Backend started (PID $($process.Id)): http://localhost:8000"
