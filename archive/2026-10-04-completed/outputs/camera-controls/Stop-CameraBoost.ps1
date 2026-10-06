$ErrorActionPreference = 'Stop'
Set-Content -LiteralPath (Join-Path $PSScriptRoot 'stop-boost.request') -Value 'Stop and restore the previous runtime camera values.'
Write-Output 'Stop requested. The helper will restore its previous values if the camera object is still valid.'
