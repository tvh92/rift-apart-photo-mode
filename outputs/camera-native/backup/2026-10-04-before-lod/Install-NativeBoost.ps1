$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before installing the native boost.' }
$taskManifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
if ((Get-FileHash -LiteralPath (Join-Path $taskGame 'RiftApart.exe') -Algorithm SHA256).Hash -ine $taskManifest.game_sha256) { throw 'Unsupported game build.' }
$taskSource = Join-Path $PSScriptRoot 'hid.dll'
if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash -ine $taskManifest.dll_sha256) { throw 'Native boost DLL hash mismatch.' }
$taskTarget = Join-Path $taskGame 'hid.dll'
if (Test-Path -LiteralPath $taskTarget) {
    $taskInstalledHash = (Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash
    $taskKnownPrior = '97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81'
    if ($taskInstalledHash -ine $taskManifest.dll_sha256 -and $taskInstalledHash -ine $taskKnownPrior) { throw 'Another HID DLL is installed. Refusing to overwrite it.' }
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
$taskManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') -Encoding utf8
Write-Output 'Native boost installed. Launch the game normally; no helper or extra launch argument is needed.'
