[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$spec = Join-Path $PSScriptRoot "neo_rating.spec"

if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$version = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($version -ne "3.12") {
    throw "Python 3.12 is required; found $version."
}

Push-Location $projectRoot
try {
    & $python -m PyInstaller --clean --noconfirm $spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$executable = Join-Path $projectRoot "dist\NEORating-0.1.0-portable\NEORating.exe"
if (-not (Test-Path -LiteralPath $executable)) {
    throw "The portable executable was not generated."
}

$distribution = Split-Path -Parent $executable
$archive = Join-Path $projectRoot "dist\NEORating-0.1.0-windows-x64.zip"
if (Test-Path -LiteralPath $archive) {
    Remove-Item -LiteralPath $archive -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $distribution,
    $archive,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $true
)

Get-FileHash -Algorithm SHA256 -LiteralPath $executable
Get-FileHash -Algorithm SHA256 -LiteralPath $archive
