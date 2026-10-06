$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskControls = Join-Path $taskRoot 'outputs\camera-controls'
$taskPackage = Join-Path $taskRoot 'outputs\startup-repair\NoIntro-Fixed-2Seconds.stage'
$taskPython = 'C:\Users\Tim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskManagers = @((Join-Path $taskRoot 'outputs\Overstrike'),'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh')
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Game or Overstrike is still running.' }
& (Join-Path $taskControls 'Assert-CleanBaseline.ps1')
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'toc') -Algorithm SHA1).Hash -ine '78ee66e82f32eedf237490a7239c8d7f7760ebff') { throw 'Unexpected current diagnostic index.' }
if ((Get-FileHash -LiteralPath $taskPackage -Algorithm SHA256).Hash -ine '5fc62afad01e5be5c66bfd92921f41bc9a9fe301bb50e22f27e48024516b74cd') { throw 'Fixed package hash differs.' }
$taskProfiles = @()
foreach ($taskManager in $taskManagers) {
    $taskProfilePath = Join-Path $taskManager 'Profiles\RCRA (Steam).json'
    $taskData = Get-Content -Raw -LiteralPath $taskProfilePath | ConvertFrom-Json
    if ($taskData.game -cne 'RCRA' -or $taskData.path -cne $taskGame -or $taskData.mods.Count -ne 2 -or $taskData.mods[0][0] -cne 'NoIntro.stage' -or $taskData.mods[1][0] -cne 'PhotoMode-10x-Tether1000.stage') { throw 'Unexpected manager profile.' }
    $taskProfiles += @{manager=$taskManager;path=$taskProfilePath;data=$taskData}
}
$taskBackup = Join-Path $taskRoot ('outputs\startup-repair\permanent-backup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskBackup | Out-Null
foreach ($taskName in @('toc','toc.sha1')) {
    $taskFile = Join-Path $taskGame $taskName
    if (Test-Path -LiteralPath $taskFile) { Copy-Item -LiteralPath $taskFile -Destination (Join-Path $taskBackup $taskName) }
}
foreach ($taskName in @('mod0','mod1')) {
    $taskFile = Join-Path $taskGame ('d\mods\'+$taskName)
    if (Test-Path -LiteralPath $taskFile) { Copy-Item -LiteralPath $taskFile -Destination (Join-Path $taskBackup $taskName) }
}
foreach ($taskIndex in 0..1) {
    $taskRow = $taskProfiles[$taskIndex]
    Copy-Item -LiteralPath $taskRow.path -Destination (Join-Path $taskBackup ('profile'+$taskIndex+'.json'))
    $taskCache = Join-Path $taskRow.manager 'Mods Library\Cache.json'
    if (Test-Path -LiteralPath $taskCache) { Copy-Item -LiteralPath $taskCache -Destination (Join-Path $taskBackup ('cache'+$taskIndex+'.json')) }
}
try {
    foreach ($taskRow in $taskProfiles) {
        Copy-Item -LiteralPath $taskPackage -Destination (Join-Path $taskRow.manager 'Mods Library\NoIntro-Fixed-2Seconds.stage') -Force
        $taskRow.data.mods=@(@('NoIntro.stage',$false),@('NoIntro-Fixed-2Seconds.stage',$true),@('PhotoMode-10x-Tether1000.stage',$true))
        $taskRow.data | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskRow.path -Encoding utf8
        $taskCache = Join-Path $taskRow.manager 'Mods Library\Cache.json'
        if (Test-Path -LiteralPath $taskCache) { Remove-Item -LiteralPath $taskCache }
    }
    $taskRun = Start-Process -FilePath (Join-Path $taskManagers[0] 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskManagers[0] -WindowStyle Hidden -Wait -PassThru
    if ($taskRun.ExitCode -ne 0) { throw 'Permanent install failed.' }
    & $taskPython (Join-Path $taskControls 'Check-Installation.py')
    if ($LASTEXITCODE -ne 0) { throw 'Permanent install audit failed.' }
} catch {
    foreach ($taskName in @('toc','toc.sha1')) {
        $taskSaved = Join-Path $taskBackup $taskName
        if (Test-Path -LiteralPath $taskSaved) { Copy-Item -LiteralPath $taskSaved -Destination (Join-Path $taskGame $taskName) -Force }
    }
    foreach ($taskName in @('mod0','mod1')) {
        $taskSaved = Join-Path $taskBackup $taskName
        if (Test-Path -LiteralPath $taskSaved) { Copy-Item -LiteralPath $taskSaved -Destination (Join-Path $taskGame ('d\mods\'+$taskName)) -Force }
    }
    foreach ($taskIndex in 0..1) {
        $taskRow=$taskProfiles[$taskIndex]
        Copy-Item -LiteralPath (Join-Path $taskBackup ('profile'+$taskIndex+'.json')) -Destination $taskRow.path -Force
        $taskSavedCache=Join-Path $taskBackup ('cache'+$taskIndex+'.json')
        if (Test-Path -LiteralPath $taskSavedCache) { Copy-Item -LiteralPath $taskSavedCache -Destination (Join-Path $taskRow.manager 'Mods Library\Cache.json') -Force }
    }
    throw
}
@{fixed_intro_enabled=$true;camera_asset_enabled=$true;legacy_nointro_disabled=$true;backup=$taskBackup;in_game_result='pending final combined launch'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot 'outputs\startup-repair\permanent-install.json') -Encoding utf8
Write-Output 'Fixed intro and camera mods installed in both managers. Clean baseline and native camera DLL preserved.'
