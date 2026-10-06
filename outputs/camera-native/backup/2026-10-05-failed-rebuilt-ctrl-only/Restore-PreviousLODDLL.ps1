$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before restoring the previous LOD DLL.' }
$taskManifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'RiftApart.exe') -Algorithm SHA256).Hash -ine $taskManifest.game_sha256) { throw 'Unsupported game build.' }
$taskPrevious = '7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272'
$taskSource = Join-Path $PSScriptRoot 'backup\2026-10-05-before-control-indicator\hid.dll'
$taskTarget = Join-Path $taskGame 'hid.dll'
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ine $taskPrevious) { throw 'Previous LOD DLL backup changed.' }
$taskInstalled = (Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash
if ($taskInstalled -ine $taskManifest.dll_sha256 -and $taskInstalled -ine $taskPrevious) { throw 'Installed DLL is unknown; refusing to overwrite it.' }
Copy-Item -LiteralPath $taskSource -Destination $taskTarget -Force
if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ine $taskPrevious) { throw 'Restored DLL hash mismatch.' }
$taskManifest.installed = $false
$taskManifest | Add-Member -NotePropertyName installed_dll_sha256 -NotePropertyValue $taskPrevious -Force
$taskManifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') -Encoding utf8
Write-Output 'Restored the previous geometry LOD DLL with Ctrl+Alt+L. No-clip, speed and asset mods remain installed.'
