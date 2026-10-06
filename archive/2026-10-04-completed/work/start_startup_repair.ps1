$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskBackup = Join-Path (Split-Path $PSScriptRoot -Parent) 'outputs\startup-repair\backup-before'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Rift Apart must be closed before repairing its index.' }
New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
foreach ($taskName in @('toc','toc.BAK','toc.sha1','PhotoModeCamera.ini','PhotoModeCamera.log','hid.dll')) {
 $taskPath = Join-Path $taskGame $taskName
 if ((Test-Path -LiteralPath $taskPath) -and -not (Test-Path -LiteralPath (Join-Path $taskBackup $taskName))) { Copy-Item -LiteralPath $taskPath -Destination (Join-Path $taskBackup $taskName) }
}
foreach ($taskName in @('mod0','mod1')) {
 $taskPath = Join-Path $taskGame ('d\mods\'+$taskName)
 if ((Test-Path -LiteralPath $taskPath) -and -not (Test-Path -LiteralPath (Join-Path $taskBackup $taskName))) { Copy-Item -LiteralPath $taskPath -Destination (Join-Path $taskBackup $taskName) }
}
$taskAllowedOverstrike = @(
 'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh\Overstrike.exe',
 (Join-Path (Split-Path $PSScriptRoot -Parent) 'outputs\Overstrike\Overstrike.exe')
)
foreach ($taskApp in @(Get-Process -Name Overstrike -ErrorAction SilentlyContinue)) {
 if ($taskApp.Path -notin $taskAllowedOverstrike) { throw ('Unexpected Overstrike process: '+$taskApp.Path) }
 $taskNativeProcess = [Diagnostics.Process]::GetProcessById($taskApp.Id)
 if (-not $taskNativeProcess.CloseMainWindow()) { throw 'Please close Overstrike to continue the repair.' }
 if (-not $taskNativeProcess.WaitForExit(5000)) { throw 'Overstrike did not close; close it to continue.' }
}
Start-Process -FilePath 'C:\Program Files (x86)\Steam\steam.exe' -ArgumentList 'steam://validate/1895880' -WindowStyle Hidden
Write-Output 'Backups saved; Steam verification requested.'
