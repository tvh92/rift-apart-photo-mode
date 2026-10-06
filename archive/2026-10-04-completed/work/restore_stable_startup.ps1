$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskOverstrike = Join-Path $taskRoot 'outputs\Overstrike'
$taskManagers = @($taskOverstrike,'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh')
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Game and Overstrike must be closed.' }
if ((Get-FileHash (Join-Path $taskGame 'toc.BAK') -Algorithm SHA1).Hash -ine '64946f571579d9ea0a17e675682e2994dc0f20fc') { throw 'Clean baseline changed.' }
$taskRows = @()
foreach ($taskManager in $taskManagers) {
 $taskProfile = Join-Path $taskManager 'Profiles\RCRA (Steam).json'
 $taskData = Get-Content -Raw -LiteralPath $taskProfile | ConvertFrom-Json
 if ($taskData.game -cne 'RCRA' -or $taskData.path -cne $taskGame -or $taskData.mods.Count -ne 3 -or $taskData.mods[0][0] -cne 'NoIntro.stage' -or $taskData.mods[0][1] -or $taskData.mods[1][0] -cne 'PhotoMode-10x-Tether1000.stage' -or -not $taskData.mods[1][1] -or $taskData.mods[2][0] -cne 'NoIntro-CurrentBuild.stage') { throw 'Unexpected profile.' }
 $taskData.mods = @($taskData.mods[0],$taskData.mods[1])
 $taskRows += @{Path=$taskProfile;Data=$taskData;Manager=$taskManager}
}
$taskBackup = Join-Path $taskRoot 'outputs\startup-repair\profiles-before-final-restore'
New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
foreach ($taskIndex in 0..1) {
 $taskRow=$taskRows[$taskIndex]
 Copy-Item -LiteralPath $taskRow.Path -Destination (Join-Path $taskBackup ('profile'+$taskIndex+'.json'))
 $taskRow.Data | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskRow.Path -Encoding utf8
}
$taskInstall = Start-Process -FilePath (Join-Path $taskOverstrike 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskOverstrike -WindowStyle Hidden -Wait -PassThru
if ($taskInstall.ExitCode -ne 0) { throw 'Original-intro restoration failed.' }
$taskStage = Join-Path $taskRoot 'outputs\startup-repair\NoIntro-CurrentBuild.stage'
$taskExpectedHash = (Get-FileHash -LiteralPath $taskStage -Algorithm SHA256).Hash
foreach ($taskManager in $taskManagers) {
 $taskLibraryStage = Join-Path $taskManager 'Mods Library\NoIntro-CurrentBuild.stage'
 if (Test-Path -LiteralPath $taskLibraryStage) {
  if ((Get-FileHash -LiteralPath $taskLibraryStage -Algorithm SHA256).Hash -ine $taskExpectedHash) { throw 'Experimental library package changed; leaving it alone.' }
  Remove-Item -LiteralPath $taskLibraryStage
 }
}
Write-Output 'Original intro movies restored. Camera mod remains enabled. Incompatible intro packages are inactive.'
