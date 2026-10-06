$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskCompiler=Join-Path $taskRoot 'work/toolchain/zig-x86_64-windows-0.15.2/zig.exe'
$env:ZIG_GLOBAL_CACHE_DIR=Join-Path $taskRoot 'work/zig-cache'
$taskCount='-DHID_EXPORT_COUNT='+((Get-Content -Raw (Join-Path $PSScriptRoot 'export-manifest.json') | ConvertFrom-Json).count)
& $taskCompiler cc -target x86_64-windows-gnu -O2 -Wall -Wextra -shared $taskCount (Join-Path $PSScriptRoot 'CameraBoost.c') (Join-Path $PSScriptRoot 'HidExports.c') (Join-Path $PSScriptRoot 'CameraStubs.S') (Join-Path $PSScriptRoot 'hid.def') -o (Join-Path $PSScriptRoot 'hid.dll') -lbcrypt -luser32 '-Wl,--nxcompat' '-Wl,--dynamicbase'
if($LASTEXITCODE -ne 0){throw 'Fog candidate DLL build failed'}
& $taskCompiler cc -target x86_64-windows-gnu -O2 -Wall -Wextra (Join-Path $taskRoot 'work/native-abi/PhotoFogProbe.c') -o (Join-Path $taskRoot 'work/native-abi/PhotoFogProbe.exe')
if($LASTEXITCODE -ne 0){throw 'Fog candidate probe build failed'}
& (Join-Path $taskRoot 'work/native-abi/PhotoFogProbe.exe')
if($LASTEXITCODE -ne 0){throw "Fog candidate probe failed with exit code $LASTEXITCODE"}
$taskPython='C:\Users\Tim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $taskPython (Join-Path $taskRoot 'work/prepare_fog_validation.py')
if($LASTEXITCODE -ne 0){throw 'Fog validation preparation failed'}
foreach($taskProbe in @('PhotoLifecycleFogIntegrationProbe','BehaviorFogIntegrationProbe')) {
    & $taskCompiler cc -target x86_64-windows-gnu -O2 -Wall -Wextra (Join-Path $taskRoot "work/native-abi/$taskProbe.c") (Join-Path $PSScriptRoot 'HidExports.c') (Join-Path $PSScriptRoot 'CameraStubs.S') -o (Join-Path $taskRoot "work/native-abi/$taskProbe.exe") -lbcrypt -luser32
    if($LASTEXITCODE -ne 0){throw "$taskProbe compilation failed"}
    & (Join-Path $taskRoot "work/native-abi/$taskProbe.exe")
    if($LASTEXITCODE -ne 0){throw "$taskProbe failed with exit code $LASTEXITCODE"}
}
Push-Location $taskRoot
try {
    & $taskPython work/test_fog_native_proxy.py
    if($LASTEXITCODE -ne 0){throw 'Fog proxy verification failed'}
} finally {Pop-Location}
