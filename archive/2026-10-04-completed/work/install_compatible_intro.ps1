$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskOverstrike = Join-Path $taskRoot 'outputs\Overstrike'
$taskDownloadOverstrike = 'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh'
$taskManagers = @($taskOverstrike,$taskDownloadOverstrike)
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Game and Overstrike must be closed.' }
if ((Get-FileHash (Join-Path $taskGame 'toc.BAK') -Algorithm SHA1).Hash -ine '64946f571579d9ea0a17e675682e2994dc0f20fc') { throw 'Clean baseline changed.' }
$taskStage = Join-Path $taskRoot 'outputs\startup-repair\NoIntro-CurrentBuild.stage'
$taskValidation = Get-Content -Raw (Join-Path $taskRoot 'outputs\startup-repair\bink-validation.json') | ConvertFrom-Json
if (@($taskValidation | Where-Object { $_.file -ne 'legacy.bk2' -and (-not $_.opened -or $_.final_frame_number -ne 4 -or $_.last_error -ne '') }).Count) { throw 'Replacement video validation failed.' }
$taskProfiles = @()
foreach ($taskManager in $taskManagers) {
 $taskProfile = Join-Path $taskManager 'Profiles\RCRA (Steam).json'
 $taskData = Get-Content -Raw -LiteralPath $taskProfile | ConvertFrom-Json
 if ($taskData.game -cne 'RCRA' -or $taskData.path -cne $taskGame -or $taskData.mods.Count -ne 2 -or $taskData.mods[0][0] -cne 'NoIntro.stage' -or $taskData.mods[0][1] -or $taskData.mods[1][0] -cne 'PhotoMode-10x-Tether1000.stage' -or -not $taskData.mods[1][1]) { throw 'Unexpected profile.' }
 $taskProfiles += @{Path=$taskProfile;Data=$taskData;Manager=$taskManager}
}
$taskBackup = Join-Path $taskRoot 'outputs\startup-repair\profiles-before-compatible-intro'
New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
foreach ($taskIndex in 0..1) {
 $taskRow=$taskProfiles[$taskIndex]
 Copy-Item -LiteralPath $taskRow.Path -Destination (Join-Path $taskBackup ('profile'+$taskIndex+'.json'))
 Copy-Item -LiteralPath $taskStage -Destination (Join-Path $taskRow.Manager 'Mods Library\NoIntro-CurrentBuild.stage') -Force
 $taskRow.Data.mods += ,@('NoIntro-CurrentBuild.stage',$true)
 $taskRow.Data | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskRow.Path -Encoding utf8
}
try {
 $taskInstall = Start-Process -FilePath (Join-Path $taskOverstrike 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskOverstrike -WindowStyle Hidden -Wait -PassThru
 if ($taskInstall.ExitCode -ne 0) { throw 'Compatible-intro installation failed.' }
} catch {
 foreach ($taskIndex in 0..1) { Copy-Item -LiteralPath (Join-Path $taskBackup ('profile'+$taskIndex+'.json')) -Destination $taskProfiles[$taskIndex].Path -Force }
 $taskRestore = Start-Process -FilePath (Join-Path $taskOverstrike 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskOverstrike -WindowStyle Hidden -Wait -PassThru
 throw
}
Write-Output 'Current-build short intro installed; legacy NoIntro remains disabled; camera mod preserved.'
