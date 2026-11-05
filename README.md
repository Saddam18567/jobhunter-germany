# JobHunter Germany 🇩🇪 - Standalone Desktop Job Search & ATS Detector

A modern, standalone desktop application designed specifically for hunting jobs in Germany. It unifies **official German government REST APIs (Bundesagentur für Arbeit)**, legal job scrapers (**JobSpy** for LinkedIn, Indeed, Glassdoor, Google Jobs), **Arbeitnow**, and an intelligent **ATS Detector** (recognizing Workday, Personio, Greenhouse, Lever, and Softgarden direct career portals).

> **No Python or server setup required.** The application is compiled with all dependencies embedded. A one-click installer configures everything and creates your Desktop and Start Menu shortcuts automatically.

---

## ✨ Features at a Glance

- **Zero Python Setup**: Runs as a self-contained desktop app with embedded runtime.
- **1-Click Standalone Installer**:
  - Automatically installs the application into your local programs directory.
  - Creates a **Desktop Shortcut** (`JobHunter Germany`).
  - Creates a **Windows Start Menu Shortcut** (`JobHunter Germany`).
  - Automatically launches the app immediately upon setup!
- **Automatic Excel Generation**:
  - Filling the search form and clicking **"Find Jobs & Generate Excel"** automatically gathers the listings, classifies ATS platforms, and generates a formatted Microsoft Excel (`.xlsx`) spreadsheet.
  - A prominent **"Open in Excel ↗"** button allows you to launch the spreadsheet directly in Microsoft Excel with one click.
  - No messy CSV files—pure, styled Excel with clickable links (`Apply Link ↗` and `View Listing ↗`), auto-filters, and zebra rows.
- **Official German Government Directory (REST API)**:
  - Official Bundesagentur für Arbeit Jobsuche REST API covering all 16 German states, administrative districts, and cities.
- **JobSpy German Aggregation**:
  - Indeed Germany (`country_indeed="germany"`), LinkedIn, Glassdoor, and Google Jobs.
- **ATS Recognition**:
  - Highlights whether jobs are on **Workday**, **Personio**, **Greenhouse**, **Lever**, **Softgarden**, or official portals, and provides actionable application guidance.

---

## 🚀 Standalone Installation on Windows (No Python Needed)

### Step 1: Download or Extract the Release Package
Extract `JobHunterGermany_Windows_Installer.zip` (located in the [`release/`](file:///data/workspace/job-hunt/release/) folder).

### Step 2: Run Setup
Double-click:
```bat
Setup.bat
```

### What happens automatically:
1. Copies all files and embedded libraries into `%LocalAppData%\JobHunterGermany`.
2. Creates a **Desktop Shortcut** on your Windows Desktop: `JobHunter Germany`.
3. Creates a **Windows Start Menu Shortcut**: `JobHunter Germany`.
4. Automatically launches the application!

### For all subsequent runs:
Just double-click the **JobHunter Germany** icon on your Desktop or search for it in your Windows Start Menu!

---

## 🛠️ How It Works

1. **Open the App**: Click the Desktop shortcut.
2. **Fill in the Search Form**:
   - **Job Title / Keyword**: e.g., *Python Developer*, *Data Engineer*, *DevOps*.
   - **German Location**: e.g., *Berlin*, *München*, *Hamburg*, *Frankfurt*, or *All Germany*.
   - **Radius (Umkreis)**: `10 km`, `25 km`, `50 km`, `100 km`, `200 km`.
   - **Contract Type**: *Full-time (Vollzeit)*, *Part-time (Teilzeit)*, *Contract / Freelance*.
   - **Remote Toggle**: Filter positions with home-office flexibility.
   - **Date Posted**: *Past 24 Hours*, *3 Days*, *7 Days*, *14 Days*, *30 Days*.
   - **Platforms**: Toggle Bundesagentur für Arbeit, Indeed, LinkedIn, Arbeitnow, Glassdoor, Google Jobs.
3. **Click "Find Jobs & Generate Excel"**:
   - The app searches all active platforms in parallel.
   - Identifies direct ATS systems (Workday, Personio, etc.).
   - Merges identical job postings.
   - **Automatically generates your Excel spreadsheet** in the `exports/` folder.
4. **View & Open**:
   - Click the green **"Open in Excel ↗"** banner to launch Microsoft Excel directly.
   - Or browse and filter the results live in the desktop table.

---

## 📦 For Developers: Building the Standalone Packages

If you are modifying code and want to rebuild the standalone Windows packages:

```bash
# 1. Compile the PyInstaller standalone binary
python build_exe.py

# 2. Package into the distribution zip with Setup.bat and shortcuts
python package_release.py
```

This creates:
- `release/JobHunterGermany_Windows_Installer.zip` (ready for end users on laptops without Python).
- `installer/installer.iss` (ready for Inno Setup compiler if you want a `.exe` installer wizard).

---

## 📁 Architecture Overview

```
job-hunt/
├── Setup.bat                   # 1-Click Windows installer (no Python needed)
├── release/
│   └── JobHunterGermany_Windows_Installer.zip  # Ready-to-distribute release package
├── installer/
│   ├── install.ps1             # Windows installer script (creates shortcuts & launches)
│   └── installer.iss           # Inno Setup wizard configuration
├── main.py                     # App entry point
├── build_exe.py                # PyInstaller standalone packager
├── package_release.py          # Release zip packager
├── config.py                   # Paths, API keys, ATS signatures
├── core/
│   ├── aggregator.py           # Parallel multi-source search
│   ├── ats_detector.py         # Workday, Personio, Greenhouse ATS classifier
│   ├── deduplicator.py         # Cross-platform job deduplication
│   ├── exporter.py             # Formatted Excel (.xlsx) generator with hyperlinks
│   ├── models.py               # Data models
│   └── sources/                # API clients (Arbeitsagentur, Arbeitnow, JobSpy)
├── exports/                    # Auto-generated Excel sheets
└── ui/
    ├── app.py                  # PyWebView window & API controller
    └── static/                 # HTML/JS/CSS frontend
```
