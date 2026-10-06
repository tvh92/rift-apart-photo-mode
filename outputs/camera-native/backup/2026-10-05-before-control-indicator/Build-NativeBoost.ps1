$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskCompiler = Join-Path $taskRoot 'work\toolchain\zig-x86_64-windows-0.15.2\zig.exe'
if (-not (Test-Path -LiteralPath $taskCompiler)) { throw 'The verified portable Zig compiler is unavailable.' }
$env:ZIG_GLOBAL_CACHE_DIR = Join-Path $taskRoot 'work\zig-cache'
$taskExports = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'export-manifest.json') | ConvertFrom-Json
$taskCount = '-DHID_EXPORT_COUNT=' + $taskExports.count
$taskArgs = @('cc','-target','x86_64-windows-gnu','-O2','-Wall','-Wextra','-shared',$taskCount,
    (Join-Path $PSScriptRoot 'CameraBoost.c'),(Join-Path $PSScriptRoot 'HidExports.c'),(Join-Path $PSScriptRoot 'CameraStubs.S'),
    (Join-Path $PSScriptRoot 'hid.def'),'-o',(Join-Path $PSScriptRoot 'hid.dll'),'-lbcrypt','-luser32','-Wl,--nxcompat','-Wl,--dynamicbase')
& $taskCompiler @taskArgs
if ($LASTEXITCODE -ne 0) { throw 'Native boost compilation failed.' }
Write-Output 'Built hid.dll. Re-run verification and update the build manifest before installing a changed DLL.'
