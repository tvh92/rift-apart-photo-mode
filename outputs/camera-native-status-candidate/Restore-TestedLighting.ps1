$ErrorActionPreference='Stop'
$taskGame='C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskManifest=Get-Content -Raw (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
$taskPrevious='fa3ced0a22083cfe0e9ee68c96e5bdda2c4d13c46f34346c79848693873356b6'
$taskTarget=Join-Path $taskGame 'hid.dll'
$taskBackup=Join-Path $PSScriptRoot 'backup/2026-10-06-before-status/hid.dll'
if(Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue){throw 'Close the game and Overstrike before rollback.'}
if((Get-FileHash (Join-Path $taskGame 'RiftApart.exe')).Hash -ine $taskManifest.game_sha256){throw 'Unsupported executable build.'}
if((Get-FileHash $taskBackup).Hash -ine $taskPrevious){throw 'Tested lighting rollback DLL hash mismatch.'}
$taskCurrent=(Get-FileHash $taskTarget).Hash
if($taskCurrent -ine $taskManifest.dll_sha256 -and $taskCurrent -ine $taskPrevious){throw 'Unknown installed DLL; refusing overwrite.'}
Copy-Item -LiteralPath $taskBackup -Destination $taskTarget -Force
if((Get-FileHash $taskTarget).Hash -ine $taskPrevious){throw 'Rollback DLL readback mismatch.'}
Write-Output 'Restored tested lighting/fog DLL with Ctrl and no indicator. Original movies, INI, assets and saves were not changed.'
