param([ValidateRange(1,1000)][int]$Normal = 10, [ValidateRange(1,1000)][int]$Boost = 100)
$ErrorActionPreference = 'Stop'
$taskPython = 'C:\Users\Tim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskScript = Join-Path $PSScriptRoot 'CameraShiftBoost.py'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'The local Python runtime is unavailable.' }
$taskGames = @(Get-Process -Name RiftApart -ErrorAction SilentlyContinue)
if ($taskGames.Count -ne 1) { throw 'Launch Rift Apart, load a level, enter Photo Mode, and select Free first.' }
$taskRunning = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*CameraShiftBoost.py*' })
if ($taskRunning.Count) { throw 'A camera helper is already running. Stop it before starting another.' }
$taskStop = Join-Path $PSScriptRoot 'stop-boost.request'
if (Test-Path -LiteralPath $taskStop) { Remove-Item -LiteralPath $taskStop }
$taskArgs = '"' + $taskScript + '" ' + $taskGames[0].Id + ' --normal ' + $Normal + ' --boost ' + $Boost
Start-Process -FilePath $taskPython -ArgumentList $taskArgs -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'boost.log') -RedirectStandardError (Join-Path $PSScriptRoot 'boost-error.log')
Write-Output 'Starting camera helper. It will identify the live Free camera before writing any values.'
Write-Output 'Hold Shift to boost; Ctrl+Alt+F10 stops the helper. Status is saved to boost-status.json.'
