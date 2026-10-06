$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before restoring the confirmed speed DLL.' }
$taskManifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'RiftApart.exe') -Algorithm SHA256).Hash -ine $taskManifest.game_sha256) { throw 'Unsupported game build.' }
$taskOriginalHash = '97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81'
$taskSource = Join-Path $PSScriptRoot 'backup\2026-10-04-before-collision\hid.dll'
$taskTarget = Join-Path $taskGame 'hid.dll'
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ine $taskOriginalHash) { throw 'Confirmed speed DLL backup changed.' }
$taskInstalledHash = (Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash
if ($taskInstalledHash -ine $taskManifest.dll_sha256 -and $taskInstalledHash -ine $taskOriginalHash) { throw 'Installed DLL is unknown; refusing to overwrite it.' }
Copy-Item -LiteralPath $taskSource -Destination $taskTarget -Force
if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ine $taskOriginalHash) { throw 'Restored DLL hash mismatch.' }
Write-Output 'Restored the user-confirmed normal/Shift speed DLL. Asset mods, profiles and settings remain installed.'
