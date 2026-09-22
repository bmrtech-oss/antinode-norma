$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot '.runtime\frontend.pid'

if (-not (Test-Path $pidFile)) {
    Write-Output 'Frontend is not running.'
    exit 0
}

$frontendPid = [int](Get-Content $pidFile -Raw).Trim()
$processIds = @($frontendPid)
$descendants = Get-CimInstance Win32_Process | Where-Object {
    $processIds -contains $_.ParentProcessId
}
while ($descendants) {
    $newProcessIds = @($descendants | Select-Object -ExpandProperty ProcessId)
    $processIds += $newProcessIds
    $descendants = Get-CimInstance Win32_Process | Where-Object {
        $processIds -contains $_.ParentProcessId -and $processIds -notcontains $_.ProcessId
    }
}

$runningProcesses = $processIds |
    Sort-Object -Descending |
    ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }
if ($runningProcesses) {
    foreach ($runningProcess in $runningProcesses) {
        Stop-Process -Id $runningProcess.Id
    }
    $runningProcesses | ForEach-Object { $_.WaitForExit(5000) | Out-Null }
    Write-Output "Frontend stopped (PID $frontendPid)."
} else {
    Write-Output "Frontend process $frontendPid was not found."
}

Remove-Item $pidFile -Force
