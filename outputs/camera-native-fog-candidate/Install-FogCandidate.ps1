$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskGame='C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart'
$taskPython=(Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe')
$taskManifest=Get-Content -Raw (Join-Path $PSScriptRoot 'build-verification.json') | ConvertFrom-Json
$taskConfirmed='5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842'
$taskTarget=Join-Path $taskGame 'hid.dll'
$taskSource=Join-Path $PSScriptRoot 'hid.dll'
if(Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue){throw 'Close the game and Overstrike before installing.'}
if($taskManifest.install_blocked_reason){throw $taskManifest.install_blocked_reason}
if((Get-FileHash (Join-Path $taskGame 'RiftApart.exe')).Hash -ine $taskManifest.game_sha256){throw 'Unsupported executable build.'}
if((Get-FileHash $taskSource).Hash -ine $taskManifest.dll_sha256){throw 'Candidate DLL does not match its validation manifest.'}
$taskInstalled=(Get-FileHash $taskTarget).Hash
if($taskInstalled -ine $taskConfirmed -and $taskInstalled -ine $taskManifest.dll_sha256){throw 'Unknown installed DLL; refusing overwrite.'}
$taskBackup=Join-Path $PSScriptRoot 'backup/2026-10-05-before-native-fog'
$taskIni=Get-FileHash (Join-Path $taskGame 'PhotoModeCamera.ini')
if($taskIni.Hash -ine '2742e230e680046e4833173c6a435822aaa319999d9626608381118ad7ff34e9'){throw 'INI changed; preserve and review it before installation.'}
Push-Location $taskRoot
try {
    & $taskPython outputs/camera-controls/Check-Installation.py | Set-Content (Join-Path $PSScriptRoot 'pre-installation-audit.json')
    if($LASTEXITCODE -ne 0){throw 'Current installation audit failed.'}
    if(-not(Test-Path (Join-Path $taskBackup 'hid.dll'))) {
        if($taskInstalled -ine $taskConfirmed){throw 'Confirmed rollback DLL missing.'}
        New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
        Copy-Item -LiteralPath $taskTarget -Destination (Join-Path $taskBackup 'hid.dll')
        Copy-Item -LiteralPath (Join-Path $taskGame 'PhotoModeCamera.ini') -Destination (Join-Path $taskBackup 'PhotoModeCamera.ini')
        if(Test-Path (Join-Path $taskGame 'PhotoModeCamera.log')){Copy-Item -LiteralPath (Join-Path $taskGame 'PhotoModeCamera.log') -Destination (Join-Path $taskBackup 'PhotoModeCamera.log')}
    }
    if((Get-FileHash (Join-Path $taskBackup 'hid.dll')).Hash -ine $taskConfirmed){throw 'Confirmed rollback hash mismatch.'}
    if(Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue){throw 'Game/manager started during preflight.'}
    try {
        Copy-Item -LiteralPath $taskSource -Destination $taskTarget -Force
        if((Get-FileHash $taskTarget).Hash -ine $taskManifest.dll_sha256){throw 'Installed DLL readback mismatch.'}
        if((Get-FileHash (Join-Path $taskGame 'PhotoModeCamera.ini')).Hash -ine $taskIni.Hash){throw 'INI changed during installation.'}
        & $taskPython outputs/camera-controls/Check-Installation.py | Set-Content (Join-Path $PSScriptRoot 'installation-audit.json')
        if($LASTEXITCODE -ne 0){throw 'Post-installation audit failed.'}
    } catch {
        if(-not(Get-Process RiftApart -ErrorAction SilentlyContinue) -and (Get-FileHash $taskTarget).Hash -ieq $taskManifest.dll_sha256) {
            Copy-Item -LiteralPath (Join-Path $taskBackup 'hid.dll') -Destination $taskTarget -Force
        }
        throw
    }
    $taskManifest.installed=$true
    $taskManifest.runtime_status='Awaiting user startup/Photo-entry/far-camera/Ctrl/exit/reentry test; isolated probes passed.'
    $taskManifest | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $PSScriptRoot 'build-verification.json') -Encoding utf8
    Write-Output 'Fog candidate installed and full audit passed. Original movies, Ctrl, INI and asset packages preserved.'
} finally {Pop-Location}
