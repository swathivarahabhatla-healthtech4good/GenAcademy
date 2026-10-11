$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.tools\cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.tools\python'
$localUv = Join-Path $PSScriptRoot '.tools\uv.exe'
$launchArgs = @('run')
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.env')) {
    $launchArgs += @('--env-file', (Join-Path $PSScriptRoot '.env'))
}
$launchArgs += @('streamlit', 'run', 'app.py')
if (Test-Path -LiteralPath $localUv) {
    & $localUv @launchArgs
} else {
    uv @launchArgs
}
