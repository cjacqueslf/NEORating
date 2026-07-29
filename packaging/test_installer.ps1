[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$installer = Join-Path $projectRoot "dist\NEORating-0.1.0-Setup.exe"
$testRoot = Join-Path $env:TEMP "NEORating-InstallerTest-$PID"
$uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\NEORating"

if (-not (Test-Path -LiteralPath $installer)) {
    throw "The installer was not generated."
}
if (Test-Path -LiteralPath $testRoot) {
    throw "The test installation directory already exists."
}
if (Test-Path -LiteralPath $uninstallKey) {
    throw "An existing NEO Rating installation is registered for this user."
}

$installed = $false
try {
    $installProcess = Start-Process `
        -FilePath $installer `
        -ArgumentList @("/S", "/D=$testRoot") `
        -PassThru `
        -Wait
    if ($installProcess.ExitCode -ne 0) {
        throw "Installer failed with exit code $($installProcess.ExitCode)."
    }
    $installed = $true

    $application = Join-Path $testRoot "NEORating.exe"
    $verifyProcess = Start-Process `
        -FilePath $application `
        -ArgumentList "--verify-package" `
        -PassThru `
        -Wait `
        -WindowStyle Hidden
    if ($verifyProcess.ExitCode -ne 0) {
        throw "Installed package verification failed with exit code $($verifyProcess.ExitCode)."
    }

    $registered = Get-ItemProperty -LiteralPath $uninstallKey
    if ([IO.Path]::GetFullPath($registered.InstallLocation) -ne [IO.Path]::GetFullPath($testRoot)) {
        throw "The registered installation directory is incorrect."
    }
}
finally {
    $uninstaller = Join-Path $testRoot "Uninstall.exe"
    if ($installed -and (Test-Path -LiteralPath $uninstaller)) {
        $uninstallProcess = Start-Process `
            -FilePath $uninstaller `
            -ArgumentList "/S" `
            -PassThru `
            -Wait
        if ($uninstallProcess.ExitCode -ne 0) {
            throw "Uninstaller failed with exit code $($uninstallProcess.ExitCode)."
        }
    }
}

$deadline = (Get-Date).AddSeconds(15)
while ((Test-Path -LiteralPath $testRoot) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 250
}
if (Test-Path -LiteralPath $testRoot) {
    throw "The test installation directory remains after uninstall."
}
if (Test-Path -LiteralPath $uninstallKey) {
    throw "The uninstall registry entry remains after uninstall."
}
