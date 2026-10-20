[CmdletBinding()]
param(
    [string]$InstallerPath,
    [string]$AppId = "NEORating",
    [string]$AppName = "NEO Rating"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$installer = Join-Path $projectRoot "dist\NEORating-0.1.0-Setup.exe"
if ($InstallerPath) { $installer = $InstallerPath }
$testRoot = Join-Path $env:TEMP "NEORating-InstallerTest-$PID"
$uninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppId"

if (-not (Test-Path -LiteralPath $installer)) {
    throw "The installer was not generated."
}
if (Test-Path -LiteralPath $testRoot) {
    throw "The test installation directory already exists."
}
if (Test-Path -LiteralPath $uninstallKey) {
    throw "An existing NEO Rating installation is registered for this user."
}

$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
$menuDirectory = Join-Path ([Environment]::GetFolderPath("Programs")) "$AppName"
if ((Test-Path -LiteralPath $desktopShortcut) -or (Test-Path -LiteralPath $menuDirectory)) {
    throw "Existing NEO Rating shortcuts must be preserved; run the test in a clean user profile."
}

$installed = $false
try {
    $installProcess = Start-Process `
        -FilePath $installer `
        -ArgumentList @("/S", "/D=$testRoot") `
        -PassThru `
        -WindowStyle Hidden `
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
        -WindowStyle Hidden `
        -Wait
    if ($verifyProcess.ExitCode -ne 0) {
        throw "Installed package verification failed with exit code $($verifyProcess.ExitCode)."
    }

    $shell = New-Object -ComObject WScript.Shell
    $fileSystem = New-Object -ComObject Scripting.FileSystemObject
    foreach ($shortcutPath in @($desktopShortcut, (Join-Path $menuDirectory "$AppName.lnk"))) {
        if (-not (Test-Path -LiteralPath $shortcutPath)) {
            throw "Installer did not create shortcut: $shortcutPath"
        }
        $shortcut = $shell.CreateShortcut($shortcutPath)
        if (-not (Test-Path -LiteralPath $shortcut.TargetPath) -or
            $fileSystem.GetFile($shortcut.TargetPath).ShortPath -ne $fileSystem.GetFile($application).ShortPath) {
            throw "Shortcut points to an incorrect application: $shortcutPath"
        }
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
            -WindowStyle Hidden `
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

if ((Test-Path -LiteralPath $desktopShortcut) -or (Test-Path -LiteralPath $menuDirectory)) {
    throw "Application shortcuts remain after uninstall."
}
Write-Output "Installation, calculation, desktop/Start menu shortcuts and uninstall verified."
