# PowerShell Standalone Installer for JobHunter Germany
# Allows the user to select their custom installation directory

$ErrorActionPreference = "Stop"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "     JobHunter Germany - Standalone Installer 🇩🇪      " -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Look for JobHunterGermany files (either in same folder or in dist/JobHunterGermany)
$SourceDir = $null
if (Test-Path "$ScriptDir\JobHunterGermany.exe") {
    $SourceDir = $ScriptDir
} elseif (Test-Path "$ScriptDir\JobHunterGermany\JobHunterGermany.exe") {
    $SourceDir = "$ScriptDir\JobHunterGermany"
} elseif (Test-Path "$ScriptDir\dist\JobHunterGermany\JobHunterGermany.exe") {
    $SourceDir = "$ScriptDir\dist\JobHunterGermany"
} elseif (Test-Path "$ScriptDir\..\dist\JobHunterGermany\JobHunterGermany.exe") {
    $SourceDir = (Resolve-Path "$ScriptDir\..\dist\JobHunterGermany").Path
}

if (-not $SourceDir) {
    Write-Host "[ERROR] Could not find 'JobHunterGermany.exe' in installer directory!" -ForegroundColor Red
    Write-Host "Please ensure the application bundle is present."
    Read-Host "Press Enter to exit..."
    exit 1
}

# --- Prompt User for Installation Directory ---
$DefaultDir = "$env:LOCALAPPDATA\JobHunterGermany"
Write-Host "Choose where to install JobHunter Germany:" -ForegroundColor White
Write-Host "Default location: $DefaultDir" -ForegroundColor Gray
Write-Host "Press [ENTER] to use default, type [B] to browse folder, or type a custom path:" -ForegroundColor Yellow
$userChoice = Read-Host "Install Path"

$InstallDir = $DefaultDir

if ([string]::IsNullOrWhiteSpace($userChoice)) {
    $InstallDir = $DefaultDir
} elseif ($userChoice.Trim().ToUpper() -eq "B") {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Select Installation Folder for JobHunter Germany"
        $folderBrowser.ShowNewFolderButton = $true
        $folderBrowser.SelectedPath = $DefaultDir

        if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK -and -not [string]::IsNullOrWhiteSpace($folderBrowser.SelectedPath)) {
            $selected = $folderBrowser.SelectedPath.Trim()
            if (-not $selected.ToLower().EndsWith("jobhuntergermany")) {
                $InstallDir = Join-Path $selected "JobHunterGermany"
            } else {
                $InstallDir = $selected
            }
        } else {
            Write-Host "No folder selected. Using default location." -ForegroundColor Gray
            $InstallDir = $DefaultDir
        }
    } catch {
        Write-Host "Folder dialog unavailable. Using default location." -ForegroundColor Gray
        $InstallDir = $DefaultDir
    }
} else {
    $InstallDir = $userChoice.Trim().Trim('"').Trim("'")
}

Write-Host ""
Write-Host "[1/4] Installing application to: $InstallDir ..." -ForegroundColor Green

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy files into chosen directory
Copy-Item -Path "$SourceDir\*" -Destination $InstallDir -Recurse -Force
Write-Host "      Files copied successfully." -ForegroundColor Gray

# Create Desktop Shortcut
Write-Host "[2/4] Creating Desktop Shortcut..." -ForegroundColor Green
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\JobHunter Germany.lnk")
$DesktopShortcut.TargetPath = "$InstallDir\JobHunterGermany.exe"
$DesktopShortcut.WorkingDirectory = "$InstallDir"
$DesktopShortcut.Description = "JobHunter Germany - AI & ATS Job Finder (Bundesagentur & JobSpy)"
$DesktopShortcut.Save()
Write-Host "      Desktop shortcut created: $DesktopPath\JobHunter Germany.lnk" -ForegroundColor Gray

# Create Start Menu Shortcut
Write-Host "[3/4] Creating Windows Start Menu Shortcut..." -ForegroundColor Green
$StartMenuPath = [Environment]::GetFolderPath("Programs")
$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuPath\JobHunter Germany.lnk")
$StartMenuShortcut.TargetPath = "$InstallDir\JobHunterGermany.exe"
$StartMenuShortcut.WorkingDirectory = "$InstallDir"
$StartMenuShortcut.Description = "JobHunter Germany - AI & ATS Job Finder"
$StartMenuShortcut.Save()
Write-Host "      Start Menu shortcut created: $StartMenuPath\JobHunter Germany.lnk" -ForegroundColor Gray

# Launch Application
Write-Host "[4/4] Launching JobHunter Germany..." -ForegroundColor Green
Start-Process -FilePath "$InstallDir\JobHunterGermany.exe" -WorkingDirectory "$InstallDir"

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  🎉 Installation Complete! Application is running.   " -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Start-Sleep -Seconds 3
