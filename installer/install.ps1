# PowerShell Standalone Installer for JobHunter Germany
# Allows the user to select their custom installation directory

param(
    [string]$TargetDir = "",
    [switch]$Silent = $false,
    [switch]$NoLaunch = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "     JobHunter Germany - Standalone Installer [DE]     " -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Look for JobHunterGermany files (either in same folder or in dist/JobHunterGermany)
$SourceDir = $null
$IsBinary = $false

if (Test-Path "$ScriptDir\JobHunterGermany.exe") {
    $SourceDir = $ScriptDir
    $IsBinary = $true
} elseif (Test-Path "$ScriptDir\JobHunterGermany\JobHunterGermany.exe") {
    $SourceDir = "$ScriptDir\JobHunterGermany"
    $IsBinary = $true
} elseif (Test-Path "$ScriptDir\dist\JobHunterGermany\JobHunterGermany.exe") {
    $SourceDir = "$ScriptDir\dist\JobHunterGermany"
    $IsBinary = $true
} elseif (Test-Path "$ScriptDir\..\dist\JobHunterGermany\JobHunterGermany.exe") {
    $SourceDir = (Resolve-Path "$ScriptDir\..\dist\JobHunterGermany").Path
    $IsBinary = $true
} elseif (Test-Path "$ScriptDir\main.py") {
    # Source mode
    $SourceDir = $ScriptDir
    $IsBinary = $false
} elseif (Test-Path "$ScriptDir\..\main.py") {
    $SourceDir = (Resolve-Path "$ScriptDir\..").Path
    $IsBinary = $false
}

if (-not $SourceDir) {
    Write-Host "[!] Could not find 'JobHunterGermany.exe' locally." -ForegroundColor Yellow
    Write-Host "[*] Attempting to download the latest Windows standalone build from GitHub..." -ForegroundColor Cyan
    
    $releaseUrl = "https://github.com/Saddam18567/jobhunter-germany/releases/latest/download/JobHunterGermany_Windows_Installer.zip"
    $tempZip = Join-Path $env:TEMP "JobHunterGermany_Download.zip"
    $tempExtract = Join-Path $env:TEMP "JobHunterGermany_Extracted"
    
    try {
        Write-Host "    Downloading: $releaseUrl ..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $releaseUrl -OutFile $tempZip -UseBasicParsing
        
        if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
        
        if (Test-Path "$tempExtract\JobHunterGermany_Installer\JobHunterGermany\JobHunterGermany.exe") {
            $SourceDir = "$tempExtract\JobHunterGermany_Installer\JobHunterGermany"
            $IsBinary = $true
        } elseif (Test-Path "$tempExtract\JobHunterGermany\JobHunterGermany.exe") {
            $SourceDir = "$tempExtract\JobHunterGermany"
            $IsBinary = $true
        }
    } catch {
        Write-Host "[ERROR] Could not auto-download Windows package: $_" -ForegroundColor Red
    }
}

if (-not $SourceDir) {
    Write-Host ""
    Write-Host "[ERROR] JobHunterGermany.exe was not found in the installer directory!" -ForegroundColor Red
    Write-Host "Please ensure you have downloaded the Windows release package from:"
    Write-Host "https://github.com/Saddam18567/jobhunter-germany/releases" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}

# --- Prompt User for Installation Directory ---
$DefaultDir = "$env:LOCALAPPDATA\JobHunterGermany"
$InstallDir = $DefaultDir

if (-not [string]::IsNullOrWhiteSpace($TargetDir)) {
    $InstallDir = $TargetDir.Trim().Trim('"').Trim("'")
    Write-Host "Target installation directory: $InstallDir" -ForegroundColor Cyan
} elseif ($Silent) {
    $InstallDir = $DefaultDir
    Write-Host "Silent mode: Using default location: $InstallDir" -ForegroundColor Cyan
} else {
    Write-Host "Choose where to install JobHunter Germany:" -ForegroundColor White
    Write-Host "Default location: $DefaultDir" -ForegroundColor Gray
    Write-Host "Press [ENTER] to use default, type [B] to browse folder, or type a custom path:" -ForegroundColor Yellow
    $userChoice = Read-Host "Install Path"

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
}

Write-Host ""
Write-Host "[1/4] Installing application to: $InstallDir ..." -ForegroundColor Green

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy files into chosen directory
Copy-Item -Path "$SourceDir\*" -Destination $InstallDir -Recurse -Force
Write-Host "      Files copied successfully." -ForegroundColor Gray

# If in source mode (not binary), set up python environment
$ExeTarget = "$InstallDir\JobHunterGermany.exe"
if (-not $IsBinary) {
    Write-Host "[*] Setting up local Python environment in $InstallDir ..." -ForegroundColor Cyan
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($pythonExe) {
        $venvDir = "$InstallDir\.venv"
        if (-not (Test-Path $venvDir)) {
            Start-Process -FilePath $pythonExe -ArgumentList "-m venv $venvDir" -Wait -NoNewWindow
        }
        $pipExe = "$venvDir\Scripts\pip.exe"
        if (Test-Path "$InstallDir\requirements.txt") {
            Start-Process -FilePath $pipExe -ArgumentList "install -r `"$InstallDir\requirements.txt`"" -Wait -NoNewWindow
        }
        $ExeTarget = "$venvDir\Scripts\pythonw.exe"
    }
}

# Create Desktop Shortcut
Write-Host "[2/4] Creating Desktop Shortcut..." -ForegroundColor Green
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\JobHunter Germany.lnk")

if ($IsBinary) {
    $DesktopShortcut.TargetPath = "$InstallDir\JobHunterGermany.exe"
    $DesktopShortcut.WorkingDirectory = "$InstallDir"
} else {
    $DesktopShortcut.TargetPath = "$InstallDir\.venv\Scripts\pythonw.exe"
    $DesktopShortcut.Arguments = "`"$InstallDir\main.py`""
    $DesktopShortcut.WorkingDirectory = "$InstallDir"
}
$DesktopShortcut.Description = "JobHunter Germany - AI & ATS Job Finder (Bundesagentur & JobSpy)"
$DesktopShortcut.Save()
Write-Host "      Desktop shortcut created: $DesktopPath\JobHunter Germany.lnk" -ForegroundColor Gray

# Create Start Menu Shortcut
Write-Host "[3/4] Creating Windows Start Menu Shortcut..." -ForegroundColor Green
$StartMenuPath = [Environment]::GetFolderPath("Programs")
$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuPath\JobHunter Germany.lnk")

if ($IsBinary) {
    $StartMenuShortcut.TargetPath = "$InstallDir\JobHunterGermany.exe"
    $StartMenuShortcut.WorkingDirectory = "$InstallDir"
} else {
    $StartMenuShortcut.TargetPath = "$InstallDir\.venv\Scripts\pythonw.exe"
    $StartMenuShortcut.Arguments = "`"$InstallDir\main.py`""
    $StartMenuShortcut.WorkingDirectory = "$InstallDir"
}
$StartMenuShortcut.Description = "JobHunter Germany - AI & ATS Job Finder"
$StartMenuShortcut.Save()
Write-Host "      Start Menu shortcut created: $StartMenuPath\JobHunter Germany.lnk" -ForegroundColor Gray

# Launch Application
if (-not $NoLaunch) {
    Write-Host "[4/4] Launching JobHunter Germany..." -ForegroundColor Green
    if ($IsBinary) {
        $proc = Start-Process -FilePath "$InstallDir\JobHunterGermany.exe" -WorkingDirectory "$InstallDir" -PassThru
        Start-Sleep -Seconds 2
        if ($proc.HasExited -and $proc.ExitCode -ne 0) {
            Write-Host "[!] Note: Process exited with code $($proc.ExitCode)." -ForegroundColor Yellow
            Write-Host "    Check $InstallDir\exports\jobhunter_debug.log or crash.log for details." -ForegroundColor Gray
            if (-not $Silent) {
                Read-Host "Press Enter to exit..."
            }
        }
    } else {
        Start-Process -FilePath "$InstallDir\.venv\Scripts\pythonw.exe" -ArgumentList "`"$InstallDir\main.py`"" -WorkingDirectory "$InstallDir"
    }
} else {
    Write-Host "[4/4] Installation finished (launch skipped via -NoLaunch)." -ForegroundColor Gray
}

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  [+] Installation Complete! Application is running.   " -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
if (-not $Silent) {
    Start-Sleep -Seconds 3
}
