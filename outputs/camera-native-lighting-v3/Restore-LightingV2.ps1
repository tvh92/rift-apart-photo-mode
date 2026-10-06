$ErrorActionPreference='Stop'
$taskGame='C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskManifest=Get-Content -Raw (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
$taskPrevious='16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd'
$taskTarget=Join-Path $taskGame 'hid.dll'
$taskBackup=Join-Path $PSScriptRoot 'backup/2026-10-06-before-cutoff/hid.dll'
if(Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue){throw 'Close the game and Overstrike before rollback.'}
if((Get-FileHash (Join-Path $taskGame 'RiftApart.exe')).Hash -ine $taskManifest.game_sha256){throw 'Unsupported executable build.'}
if((Get-FileHash $taskBackup).Hash -ine $taskPrevious){throw 'Lighting-v2 rollback DLL hash mismatch.'}
$taskCurrent=(Get-FileHash $taskTarget).Hash
if($taskCurrent -ine $taskManifest.dll_sha256 -and $taskCurrent -ine $taskPrevious){throw 'Unknown installed DLL; refusing overwrite.'}
Copy-Item -LiteralPath $taskBackup -Destination $taskTarget -Force
if((Get-FileHash $taskTarget).Hash -ine $taskPrevious){throw 'Rollback DLL readback mismatch.'}
Write-Output 'Restored lighting-v2 DLL 16dcd440. Original movies, INI, assets and saves were not changed.'
