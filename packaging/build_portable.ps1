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

$compilerCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "NSIS\makensis.exe"),
    (Join-Path $env:ProgramFiles "NSIS\makensis.exe")
)
$compiler = $compilerCandidates |
    Where-Object { $_ -and (Test-Path -LiteralPath $_) } |
    Select-Object -First 1
if (-not $compiler) {
    throw "NSIS 3.12 compiler was not found."
}

$installerScript = Join-Path $PSScriptRoot "installer.nsi"
& $compiler `
    "/DPORTABLE_DIR=$distribution" `
    "/DOUTPUT_DIR=$(Join-Path $projectRoot 'dist')" `
    $installerScript
if ($LASTEXITCODE -ne 0) {
    throw "NSIS failed with exit code $LASTEXITCODE."
}

$installer = Join-Path $projectRoot "dist\NEORating-0.1.0-Setup.exe"
$installerHash = Get-FileHash -Algorithm SHA256 -LiteralPath $installer
$installerInfo = Get-Item -LiteralPath $installer
$updateManifest = [ordered]@{
    schema_version = 1
    version = "0.1.0"
    digest2_version = "2.8.1"
    asset_name = $installerInfo.Name
    asset_size = $installerInfo.Length
    asset_sha256 = $installerHash.Hash.ToLowerInvariant()
}
$manifestPath = Join-Path $projectRoot "dist\neo-rating-update.json"
$manifestJson = $updateManifest | ConvertTo-Json
[IO.File]::WriteAllText(
    $manifestPath,
    $manifestJson + [Environment]::NewLine,
    [Text.UTF8Encoding]::new($false)
)

$installerHash
Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath

$checksumLines = @($installer, $archive, $manifestPath) | ForEach-Object {
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_
    "{0}  {1}" -f $hash.Hash.ToLowerInvariant(), (Split-Path -Leaf $_)
}
[IO.File]::WriteAllLines(
    (Join-Path $projectRoot "dist\SHA256SUMS.txt"),
    [string[]]$checksumLines,
    [Text.UTF8Encoding]::new($false)
)
