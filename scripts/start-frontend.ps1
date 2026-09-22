$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $repoRoot '.runtime'
$pidFile = Join-Path $runtimeDir 'frontend.pid'
$logFile = Join-Path $runtimeDir 'frontend.log'
$errorLogFile = Join-Path $runtimeDir 'frontend.error.log'

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

if (Test-Path $pidFile) {
    $existingPid = [int](Get-Content $pidFile -Raw).Trim()
    $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if ($existingProcess) {
        Write-Output "Frontend is already running (PID $existingPid)."
        exit 0
    }
    Remove-Item $pidFile -Force
}

$process = Start-Process `
    -FilePath 'npm.cmd' `
    -ArgumentList 'run', 'dev', '--', '--host', '0.0.0.0' `
    -WorkingDirectory (Join-Path $repoRoot 'ui') `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errorLogFile `
    -PassThru

$process.Id | Set-Content $pidFile
Write-Output "Frontend started (PID $($process.Id)): http://localhost:3000"
