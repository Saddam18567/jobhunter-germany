"""Automated PyInstaller Build Script for JobHunter Germany."""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("=======================================================")
    print("      Building JobHunter Germany Standalone App [DE]   ")
    print("=======================================================")
    print(f"Platform: {platform.system()} ({platform.machine()})")
    print(f"Python:   {sys.version.split()[0]}")
    print("-------------------------------------------------------")

    # Ensure requirements are installed
    static_folder = BASE_DIR / "ui" / "static"
    if not static_folder.exists():
        print(f"[ERROR] Static folder not found at {static_folder}")
        sys.exit(1)

    # Determine data separator (; on Windows, : on Linux/macOS)
    sep = ";" if platform.system() == "Windows" else ":"
    data_arg = f"{static_folder}{sep}ui/static"

    # PyInstaller arguments
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",             # Creates an application directory (fast startup)
        "--windowed",           # Hides the console window on launch
        "--name", "JobHunterGermany",
        "--add-data", data_arg,
        "--collect-all", "curl_cffi",
        "--collect-all", "jobspy",
        "--collect-all", "webview",
        "--collect-all", "certifi",
        "--collect-all", "requests",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pandas",
        "--hidden-import", "requests",
        "--hidden-import", "bs4",
        "--hidden-import", "certifi",
        "--hidden-import", "proxy_tools",
    ]

    if platform.system() == "Windows":
        cmd.extend([
            "--collect-all", "pythonnet",
            "--collect-all", "clr_loader",
            "--hidden-import", "clr",
            "--hidden-import", "System",
            "--hidden-import", "pythonnet",
            "--hidden-import", "clr_loader",
            "--hidden-import", "webview.platforms.winforms",
            "--hidden-import", "webview.platforms.win32",
            "--hidden-import", "webview.platforms.edgechromium",
            "--hidden-import", "webview.platforms.mshtml",
        ])

    cmd.append(str(BASE_DIR / "main.py"))

    print("[*] Running PyInstaller command:")
    print("    " + " ".join(cmd))
    print("-------------------------------------------------------")

    ret = subprocess.run(cmd, cwd=str(BASE_DIR))
    if ret.returncode != 0:
        print("[ERROR] Build failed! Check PyInstaller output above.")
        sys.exit(ret.returncode)

    dist_dir = BASE_DIR / "dist" / "JobHunterGermany"
    exe_name = "JobHunterGermany.exe" if platform.system() == "Windows" else "JobHunterGermany"
    exe_path = dist_dir / exe_name

    print("\n=======================================================")
    print("  [+] Build Completed Successfully!")
    print("=======================================================")
    print(f"Application directory: {dist_dir}")
    print(f"Executable binary:     {exe_path}")
    print("You can distribute the 'JobHunterGermany' folder or create an installer.")
    print("=======================================================\n")

if __name__ == "__main__":
    build()
