$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot '.runtime\backend.pid'

if (-not (Test-Path $pidFile)) {
    Write-Output 'Backend is not running.'
    exit 0
}

$backendPid = [int](Get-Content $pidFile -Raw).Trim()
$process = Get-Process -Id $backendPid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $backendPid
    $process.WaitForExit(5000) | Out-Null
    Write-Output "Backend stopped (PID $backendPid)."
} else {
    Write-Output "Backend process $backendPid was not found."
}

Remove-Item $pidFile -Force
