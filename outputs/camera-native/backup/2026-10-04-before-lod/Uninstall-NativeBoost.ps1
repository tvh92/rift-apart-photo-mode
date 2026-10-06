$ErrorActionPreference = 'Stop'
$taskGame = 'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
if (Get-Process -Name RiftApart -ErrorAction SilentlyContinue) { throw 'Close Rift Apart before removing the native boost.' }
$taskManifest = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
$taskTarget = Join-Path $taskGame 'hid.dll'
if (Test-Path -LiteralPath $taskTarget) {
    if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ine $taskManifest.dll_sha256) { throw 'HID DLL changed; refusing to remove another mod.' }
    Remove-Item -LiteralPath $taskTarget
}
$taskManifest.installed = $false
$taskManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build-verification.json') -Encoding utf8
Write-Output 'Native boost removed. The Overstrike asset mod still supplies the fixed 10x speed and 1000 tether.'
