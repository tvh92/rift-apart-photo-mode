$ErrorActionPreference = 'Stop'
# The original one-off migration below is retained as historical evidence.
# Route repeat use through the guarded camera-only installer instead.
& (Join-Path (Split-Path $PSScriptRoot -Parent) 'outputs\camera-controls\Reinstall-Camera.ps1')
exit
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'outputs\camera-controls'
$taskOverstrike = Join-Path (Split-Path $PSScriptRoot -Parent) 'outputs\Overstrike'
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Game and Overstrike must be closed.' }
& (Join-Path $taskRoot 'Assert-CleanBaseline.ps1')
$taskBackup = Join-Path $taskRoot 'migration-backup'
New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
$taskProfile = Join-Path $taskOverstrike 'Profiles\RCRA (Steam).json'
foreach ($taskName in @('toc','toc.BAK')) {
    $taskSource = Join-Path $taskGame $taskName
    $taskDestination = Join-Path $taskBackup $taskName
    if ((Test-Path -LiteralPath $taskSource) -and -not (Test-Path -LiteralPath $taskDestination)) { Copy-Item -LiteralPath $taskSource -Destination $taskDestination }
}
$taskSavedProfile = Join-Path $taskBackup 'RCRA (Steam).json'
if (-not (Test-Path -LiteralPath $taskSavedProfile)) { Copy-Item -LiteralPath $taskProfile -Destination $taskSavedProfile }
Copy-Item -LiteralPath (Join-Path $taskRoot 'PhotoMode-10x-Tether1000.stage') -Destination (Join-Path $taskOverstrike 'Mods Library\PhotoMode-10x-Tether1000.stage') -Force
$taskData = Get-Content -Raw -LiteralPath $taskProfile | ConvertFrom-Json
if ($taskData.game -cne 'RCRA' -or $taskData.path -cne $taskGame) { throw 'Unexpected profile target.' }
$taskAlreadyListed = @($taskData.mods | Where-Object { $_[0] -eq 'PhotoMode-10x-Tether1000.stage' })
if (-not $taskAlreadyListed.Count) { $taskData.mods += ,@('PhotoMode-10x-Tether1000.stage', $true) }
$taskData | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskProfile -Encoding utf8
try {
    & (Join-Path $taskRoot 'Set-CameraSpeed.ps1') -Multiplier Vanilla
    $taskInstall = Start-Process -FilePath (Join-Path $taskOverstrike 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskOverstrike -WindowStyle Hidden -Wait -PassThru
    if ($taskInstall.ExitCode -ne 0) { throw ('Overstrike installation failed with ' + $taskInstall.ExitCode) }
} catch {
    Copy-Item -LiteralPath $taskSavedProfile -Destination $taskProfile -Force
    Copy-Item -LiteralPath (Join-Path $taskBackup 'toc') -Destination (Join-Path $taskGame 'toc') -Force
    & (Join-Path $taskRoot 'Set-CameraSpeed.ps1') -Multiplier 10
    throw
}
Write-Output 'Overstrike migration completed; asset verification follows.'
