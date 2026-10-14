$ErrorActionPreference='Stop'
$taskRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$taskCompiler=Join-Path $taskRoot 'work/toolchain/zig-x86_64-windows-0.15.2/zig.exe'
$env:ZIG_GLOBAL_CACHE_DIR=Join-Path $taskRoot 'work/zig-cache'
$taskCount='-DHID_EXPORT_COUNT='+((Get-Content -Raw (Join-Path $PSScriptRoot 'export-manifest.json') | ConvertFrom-Json).count)
& $taskCompiler cc -target x86_64-windows-gnu -O2 -Wall -Wextra -shared $taskCount (Join-Path $PSScriptRoot 'CameraBoost.c') (Join-Path $PSScriptRoot 'HidExports.c') (Join-Path $PSScriptRoot 'CameraStubs.S') (Join-Path $PSScriptRoot 'hid.def') -o (Join-Path $PSScriptRoot 'hid.dll') -lbcrypt -luser32 '-Wl,--nxcompat' '-Wl,--dynamicbase'
if($LASTEXITCODE -ne 0){throw 'Lighting candidate DLL build failed'}
$taskPython=(Join-Path $PSScriptRoot '..\..\..\.venv\Scripts\python.exe')
& $taskPython (Join-Path $taskRoot 'work/prepare_light_validation.py')
if($LASTEXITCODE -ne 0){throw 'Lighting validation preparation failed'}
foreach($taskProbe in @('PhotoLightProbe','PhotoFogLightIntegrationProbe','PhotoLifecycleLightIntegrationProbe','BehaviorLightIntegrationProbe')) {
    $taskArgs=@('cc','-target','x86_64-windows-gnu','-O2','-Wall','-Wextra',(Join-Path $taskRoot "work/native-abi/$taskProbe.c"))
    if($taskProbe -in @('PhotoLifecycleLightIntegrationProbe','BehaviorLightIntegrationProbe')) {
        $taskArgs+=@((Join-Path $PSScriptRoot 'HidExports.c'),(Join-Path $PSScriptRoot 'CameraStubs.S'),'-lbcrypt','-luser32')
    }
    $taskArgs+=@('-o',(Join-Path $taskRoot "work/native-abi/$taskProbe.exe"))
    & $taskCompiler @taskArgs
    if($LASTEXITCODE -ne 0){throw "$taskProbe compilation failed"}
    & (Join-Path $taskRoot "work/native-abi/$taskProbe.exe")
    if($LASTEXITCODE -ne 0){throw "$taskProbe failed with exit code $LASTEXITCODE"}
}
Push-Location $taskRoot
try {
    & $taskPython work/test_light_native_proxy.py
    if($LASTEXITCODE -ne 0){throw 'Lighting proxy verification failed'}
} finally {Pop-Location}
