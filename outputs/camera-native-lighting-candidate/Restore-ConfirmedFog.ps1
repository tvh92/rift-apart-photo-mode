$ErrorActionPreference='Stop'
$taskGame='C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskManifest=Get-Content -Raw (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
$taskConfirmed='228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a'
$taskTarget=Join-Path $taskGame 'hid.dll'
$taskBackup=Join-Path $PSScriptRoot 'backup/2026-10-05-before-native-lighting/hid.dll'
if(Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue){throw 'Close the game and Overstrike before rollback.'}
if((Get-FileHash (Join-Path $taskGame 'RiftApart.exe')).Hash -ine $taskManifest.game_sha256){throw 'Unsupported executable build.'}
if((Get-FileHash $taskBackup).Hash -ine $taskConfirmed){throw 'Confirmed rollback DLL hash mismatch.'}
$taskCurrent=(Get-FileHash $taskTarget).Hash
if($taskCurrent -ine $taskManifest.dll_sha256 -and $taskCurrent -ine $taskConfirmed){throw 'Unknown installed DLL; refusing overwrite.'}
Copy-Item -LiteralPath $taskBackup -Destination $taskTarget -Force
if((Get-FileHash $taskTarget).Hash -ine $taskConfirmed){throw 'Rollback DLL readback mismatch.'}
Write-Output 'Restored user-confirmed fog DLL with Ctrl. Original movies, INI, assets and saves were not changed.'
