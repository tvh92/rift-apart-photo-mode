$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before installing the native boost.' }
$taskManifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
if ($taskManifest.install_blocked_reason) { throw $taskManifest.install_blocked_reason }
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'RiftApart.exe') -Algorithm SHA256).Hash -ine $taskManifest.game_sha256) { throw 'Unsupported game build.' }
$taskSource = Join-Path $PSScriptRoot 'hid.dll'
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ine $taskManifest.dll_sha256) { throw 'Native boost DLL hash mismatch.' }
$taskTarget = Join-Path $taskGame 'hid.dll'
if (Test-Path -LiteralPath $taskTarget) {
    $taskInstalledHash = (Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash
    $taskKnownPrior = '97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81'
    $taskConfirmedNoClip = 'ccbcdaeacb5525e05a68ede9924164f07f5d3c93e1ed6e189168bbfd8f9c8ff3'
    $taskPriorGeometry = '7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272'
    if ($taskInstalledHash -ine $taskManifest.dll_sha256 -and $taskInstalledHash -ine $taskKnownPrior -and $taskInstalledHash -ine $taskConfirmedNoClip -and $taskInstalledHash -ine $taskPriorGeometry) { throw 'Another HID DLL is installed. Refusing to overwrite it.' }
    if ($taskInstalledHash -ieq $taskPriorGeometry) {
        $taskGeometryBackup = Join-Path $PSScriptRoot 'backup\2026-10-05-before-control-indicator\hid.dll'
        if ((Get-FileHash -LiteralPath $taskGeometryBackup -Algorithm SHA256).Hash -ine $taskPriorGeometry) { throw 'Verified geometry DLL backup is missing or changed.' }
    }
    if ($taskInstalledHash -ieq $taskConfirmedNoClip) {
        $taskNoClipBackup = Join-Path $PSScriptRoot 'backup\2026-10-04-before-lod\hid.dll'
        if ((Get-FileHash -LiteralPath $taskNoClipBackup -Algorithm SHA256).Hash -ine $taskConfirmedNoClip) { throw 'Verified no-clip DLL backup is missing or changed.' }
    }
    if ($taskInstalledHash -ieq $taskKnownPrior) {
        $taskBackup = Join-Path $PSScriptRoot 'backup\2026-10-04-before-collision\hid.dll'
        if ((Get-FileHash -LiteralPath $taskBackup -Algorithm SHA256).Hash -ine $taskKnownPrior) { throw 'Verified previous DLL backup is missing or changed.' }
    }
}
Copy-Item -LiteralPath $taskSource -Destination $taskTarget -Force
$taskSettings = Join-Path $taskGame 'PhotoModeCamera.ini'
if (-not (Test-Path -LiteralPath $taskSettings)) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'PhotoModeCamera.ini') -Destination $taskSettings }
if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ine $taskManifest.dll_sha256) { throw 'Installed native boost DLL hash mismatch.' }
$taskManifest.installed = $true
$taskManifest | Add-Member -NotePropertyName installed_dll_sha256 -NotePropertyValue $taskManifest.dll_sha256 -Force
$taskManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') -Encoding utf8
Write-Output 'Native boost installed. Launch the game normally; no helper or extra launch argument is needed.'
