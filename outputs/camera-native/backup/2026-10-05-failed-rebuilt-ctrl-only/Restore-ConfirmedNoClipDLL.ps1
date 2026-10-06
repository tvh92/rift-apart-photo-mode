$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before restoring the confirmed no-clip DLL.' }
$taskManifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'RiftApart.exe') -Algorithm SHA256).Hash -ine $taskManifest.game_sha256) { throw 'Unsupported game build.' }
$taskConfirmed = 'ccbcdaeacb5525e05a68ede9924164f07f5d3c93e1ed6e189168bbfd8f9c8ff3'
$taskSource = Join-Path $PSScriptRoot 'backup\2026-10-04-before-lod\hid.dll'
$taskTarget = Join-Path $taskGame 'hid.dll'
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ine $taskConfirmed) { throw 'Confirmed no-clip DLL backup changed.' }
$taskInstalled = (Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash
if ($taskInstalled -ine $taskManifest.dll_sha256 -and $taskInstalled -ine $taskConfirmed -and $taskInstalled -ine '7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272') { throw 'Installed DLL is unknown; refusing to overwrite it.' }
Copy-Item -LiteralPath $taskSource -Destination $taskTarget -Force
if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ine $taskConfirmed) { throw 'Restored DLL hash mismatch.' }
$taskManifest.installed = $false
$taskManifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') -Encoding utf8
Write-Output 'Restored the user-confirmed no-clip and normal/Shift speed DLL. Asset mods, profiles and settings remain installed.'
