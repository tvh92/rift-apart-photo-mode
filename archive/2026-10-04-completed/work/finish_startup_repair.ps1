$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskRepair = Join-Path $taskRoot 'outputs\startup-repair'
$taskOverstrike = Join-Path $taskRoot 'outputs\Overstrike'
$taskReference = Get-Content -Raw (Join-Path $taskRepair 'steam-toc-reference.json') | ConvertFrom-Json
if (Get-Process -Name RiftApart,Overstrike -ErrorAction SilentlyContinue) { throw 'Rift Apart and Overstrike must be closed.' }
$taskManifest = Get-Content -Raw 'C:\Program Files (x86)\Steam\steamapps\appmanifest_1895880.acf'
if ($taskManifest -notmatch '"StateFlags"\s+"4"') { throw 'Steam verification/update has not completed.' }
$taskToc = Join-Path $taskGame 'toc'
if ((Get-FileHash -LiteralPath $taskToc -Algorithm SHA1).Hash -ine $taskReference.sha1) { throw 'The game index does not match the current Steam depot; cannot use it as the clean baseline.' }
$taskClean = Join-Path $taskRepair 'toc.steam-original'
if (Test-Path -LiteralPath $taskClean) {
 if ((Get-FileHash -LiteralPath $taskClean -Algorithm SHA1).Hash -ine $taskReference.sha1) { throw 'Existing clean-index backup is unexpected.' }
} else { Copy-Item -LiteralPath $taskToc -Destination $taskClean }
$taskCameraHash = '97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81'
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'hid.dll') -Algorithm SHA256).Hash -ine $taskCameraHash) { throw 'Camera DLL changed unexpectedly.' }
Copy-Item -LiteralPath $taskClean -Destination (Join-Path $taskGame 'toc.BAK') -Force
$taskProfile = Join-Path $taskOverstrike 'Profiles\RCRA (Steam).json'
$taskData = Get-Content -Raw -LiteralPath $taskProfile | ConvertFrom-Json
if ($taskData.game -cne 'RCRA' -or $taskData.path -cne $taskGame) { throw 'Unexpected profile.' }
if ($taskData.mods.Count -ne 2 -or $taskData.mods[0][0] -cne 'NoIntro.stage' -or $taskData.mods[1][0] -cne 'PhotoMode-10x-Tether1000.stage' -or -not $taskData.mods[0][1] -or -not $taskData.mods[1][1]) { throw 'Profile mod list changed unexpectedly.' }
try {
 $taskInstall = Start-Process -FilePath (Join-Path $taskOverstrike 'Overstrike.exe') -ArgumentList 'install-mods "RCRA (Steam)"' -WorkingDirectory $taskOverstrike -WindowStyle Hidden -Wait -PassThru
 if ($taskInstall.ExitCode -ne 0) { throw ('Overstrike failed with exit code '+$taskInstall.ExitCode) }
 if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'toc.BAK') -Algorithm SHA1).Hash -ine $taskReference.sha1) { throw 'Overstrike clean baseline changed unexpectedly.' }
} catch {
 Copy-Item -LiteralPath $taskClean -Destination $taskToc -Force
 throw
}
Write-Output 'Reinstalled both mods from the Steam-verified clean index; native camera DLL preserved.'
