$ErrorActionPreference='Stop'
$taskGame='C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskManifest=Get-Content -Raw (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
$taskConfirmed='5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842'
$taskTarget=Join-Path $taskGame 'hid.dll'
$taskBackup=Join-Path $PSScriptRoot 'backup/2026-10-05-before-native-fog/hid.dll'
if(Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue){throw 'Close the game and Overstrike before rollback.'}
if((Get-FileHash (Join-Path $taskGame 'RiftApart.exe')).Hash -ine $taskManifest.game_sha256){throw 'Unsupported executable build.'}
if((Get-FileHash $taskBackup).Hash -ine $taskConfirmed){throw 'Confirmed rollback DLL hash mismatch.'}
$taskCurrent=(Get-FileHash $taskTarget).Hash
if($taskCurrent -ine $taskManifest.dll_sha256 -and $taskCurrent -ine $taskConfirmed){throw 'Unknown installed DLL; refusing overwrite.'}
Copy-Item -LiteralPath $taskBackup -Destination $taskTarget -Force
if((Get-FileHash $taskTarget).Hash -ine $taskConfirmed){throw 'Rollback DLL readback mismatch.'}
Write-Output 'Restored user-confirmed Ctrl DLL. Original movies, INI, assets and saves were not changed.'
