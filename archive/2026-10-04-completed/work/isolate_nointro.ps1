$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskOverstrike = Join-Path $taskRoot 'outputs\Overstrike'
$taskProfiles = @(
 (Join-Path $taskOverstrike 'Profiles\RCRA (Steam).json'),
 'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh\Profiles\RCRA (Steam).json'
)
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Game and Overstrike must be closed.' }
if ((Get-FileHash (Join-Path $taskGame 'toc.BAK') -Algorithm SHA1).Hash -ine '64946f571579d9ea0a17e675682e2994dc0f20fc') { throw 'Clean baseline changed.' }
$taskRows = @()
foreach ($taskProfile in $taskProfiles) {
 $taskData = Get-Content -Raw -LiteralPath $taskProfile | ConvertFrom-Json
 if ($taskData.game -cne 'RCRA' -or $taskData.path -cne $taskGame -or $taskData.mods.Count -ne 2 -or $taskData.mods[0][0] -cne 'NoIntro.stage' -or $taskData.mods[1][0] -cne 'PhotoMode-10x-Tether1000.stage') { throw 'Unexpected profile mod list.' }
 $taskData.mods[0][1] = $false
 $taskRows += @{ Path=$taskProfile; Data=$taskData }
}
$taskBackup = Join-Path $taskRoot 'outputs\startup-repair\profiles-before-isolation'
New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
foreach ($taskIndex in 0..1) {
 $taskRow=$taskRows[$taskIndex]
 Copy-Item -LiteralPath $taskRow.Path -Destination (Join-Path $taskBackup ('profile'+$taskIndex+'.json'))
 $taskRow.Data | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $taskRow.Path -Encoding utf8
}
$taskInstall = Start-Process -FilePath (Join-Path $taskOverstrike 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskOverstrike -WindowStyle Hidden -Wait -PassThru
if ($taskInstall.ExitCode -ne 0) { throw 'Overstrike isolation installation failed.' }
Write-Output 'NoIntro disabled in both Overstrike profiles; camera mod remains enabled.'
