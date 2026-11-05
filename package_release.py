"""Package JobHunter Germany standalone bundle into a ready-to-distribute Windows Installer zip."""

import os
import sys
import shutil
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_APP = BASE_DIR / "dist" / "JobHunterGermany"
RELEASE_DIR = BASE_DIR / "release"
STAGING_DIR = RELEASE_DIR / "JobHunterGermany_Installer"

README_TEXT = """===============================================================
  🇩🇪 JobHunter Germany - Standalone Desktop Application
===============================================================

HOW TO INSTALL (No Python or server setup required):
---------------------------------------------------------------
1. Double-click "Setup.bat"
2. The installer will:
   - Install JobHunter Germany to your local apps directory
   - Create a shortcut on your Windows Desktop
   - Create a shortcut in your Windows Start Menu
   - Automatically launch the application!

AFTER INSTALLATION:
---------------------------------------------------------------
You can launch the app at any time directly from your:
- Desktop shortcut ("JobHunter Germany")
- Windows Start Menu

HOW IT WORKS:
---------------------------------------------------------------
- Fill in your desired position and German location (e.g. Berlin, München)
- Click "Find Jobs & Generate Excel"
- The app aggregates Bundesagentur für Arbeit (Official API), Indeed,
  LinkedIn, Arbeitnow, and identifies direct Workday & Personio ATS links.
- It automatically creates a styled Microsoft Excel (.xlsx) file in
  your exports folder and provides a 1-click button to open it immediately!

Enjoy your job hunt in Germany!
===============================================================
"""

def package():
    print("=======================================================")
    print("    Packaging JobHunter Germany Windows Release 🇩🇪    ")
    print("=======================================================")

    if not DIST_APP.exists():
        print("[*] Compiled binary not found in dist/. Running build_exe.py first...")
        from build_exe import build
        build()

    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy app bundle
    print("[1/4] Copying compiled application files...")
    target_app_dir = STAGING_DIR / "JobHunterGermany"
    shutil.copytree(DIST_APP, target_app_dir)

    # 2. Copy Setup.bat and install.ps1
    print("[2/4] Copying installer scripts...")
    shutil.copy(BASE_DIR / "Setup.bat", STAGING_DIR / "Setup.bat")
    shutil.copy(BASE_DIR / "installer" / "install.ps1", STAGING_DIR / "install.ps1")

    # 3. Add instructions
    print("[3/4] Adding user instructions...")
    with open(STAGING_DIR / "README_FIRST.txt", "w", encoding="utf-8") as f:
        f.write(README_TEXT)

    # 4. Create ZIP
    zip_path = RELEASE_DIR / "JobHunterGermany_Windows_Installer.zip"
    print(f"[4/4] Creating distribution ZIP: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(STAGING_DIR):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(RELEASE_DIR)
                zf.write(full_path, arcname=str(rel_path))

    print("\n=======================================================")
    print("  🎉 Release Package Created Successfully!")
    print("=======================================================")
    print(f"Zip File:      {zip_path}")
    print(f"Installer Dir: {STAGING_DIR}")
    print(f"File Size:     {zip_path.stat().st_size / (1024*1024):.2f} MB")
    print("=======================================================\n")

if __name__ == "__main__":
    package()
