# JobHunter Germany 🇩🇪 - Standalone Desktop Job Search & ATS Detector

A modern, standalone desktop application designed specifically for hunting jobs in Germany. It unifies **official German government REST APIs (Bundesagentur für Arbeit)**, legal job scrapers (**JobSpy** for LinkedIn, Indeed, Glassdoor, Google Jobs), **Arbeitnow**, and an intelligent **ATS Detector** (recognizing Workday, Personio, Greenhouse, Lever, and Softgarden direct career portals).

> **Zero Python Setup Required:** The application is packaged with all dependencies embedded. A standalone installer lets you choose your installation location and creates your Desktop and Start Menu shortcuts automatically.

---

## ✨ What's New in v1.1.0

- 🎯 **Multi-Keyword Search**:
  - Enter multiple job titles or skills separated by commas, semicolons, or clicking preset chips (e.g. `Python Developer, Data Engineer, DevOps Engineer`).
  - Searches all platforms concurrently for each keyword, merges duplicates, and includes a **"Matched Keywords"** column in Excel.
- 📁 **Custom Excel Save Location**:
  - Choose exactly where generated Excel spreadsheets are saved (e.g., your *Desktop*, *Downloads*, or *Documents* folder).
  - Built-in `📁 Browse` folder picker saves your folder preference permanently.
- 💻 **Custom Installation Directory**:
  - `Setup.bat` prompts you to choose your installation directory (press Enter for default `%LocalAppData%\JobHunterGermany`, type `B` to browse, or enter any custom path).
- 📊 **Pure Excel Output**:
  - Automatic generation of formatted Microsoft Excel (`.xlsx`) workbooks with styled headers, clickable application links (`Apply Link ↗`), auto-filters, and zebra striping.

---

## 🚀 Standalone Installation on Windows (No Python Needed)

### Step 1: Download & Extract
Download **[`JobHunterGermany_Windows_Installer.zip`](https://github.com/Saddam18567/jobhunter-germany/releases)** and extract the zip file.

### Step 2: Run Setup
Double-click:
```bat
Setup.bat
```

### Step 3: Choose Installation Location
When prompted in the terminal:
* Press **[ENTER]** to install to the default location (`%LocalAppData%\JobHunterGermany`).
* Type **[B]** to open the Windows folder browser dialog and pick a folder visually.
* Or type any custom folder path (e.g. `D:\Software\JobHunterGermany`).

The installer will:
1. Copy all application files to your chosen path.
2. Create a **Desktop Shortcut**: `JobHunter Germany.lnk`.
3. Create a **Windows Start Menu Shortcut**: `JobHunter Germany.lnk`.
4. Automatically launch the application!

---

## 🖥️ How It Works

1. **Open the App**: Click the Desktop shortcut or launch from Windows Start Menu.
2. **Configure Your Search**:
   - **Job Titles / Keywords**: Enter one or more comma-separated keywords (e.g. `Python Developer, Data Engineer`) or click the `+` preset chips.
   - **Location**: Enter a German city (e.g. `Berlin`, `München`) or click `All Germany`.
   - **Excel Save Location**: Click `📁 Browse` to pick your preferred destination folder.
   - **Radius (Umkreis)**: `10 km`, `25 km`, `50 km`, `100 km`, `200 km`.
   - **Contract Type & Remote**: Filter by *Vollzeit*, *Teilzeit*, or *Remote / Home Office*.
   - **Platforms**: Toggle Bundesagentur für Arbeit, Indeed Germany, LinkedIn, Arbeitnow, Glassdoor, Google Jobs.
3. **Click "Find Jobs & Generate Excel"**:
   - Gathers listings from all platforms for all specified keywords.
   - Identifies direct ATS systems (**Workday**, **Personio**, **Greenhouse**, **Lever**, **Softgarden**).
   - Merges identical job postings and tags which keyword(s) matched.
   - Automatically writes the formatted `.xlsx` workbook to your chosen save location.
4. **Open Spreadsheet**:
   - Click **"Open in Excel ↗"** to launch Microsoft Excel immediately.

---

## 📁 Repository Structure

```
job-hunt/
├── Setup.bat                   # Standalone 1-click Windows installer
├── release/
│   └── JobHunterGermany_Windows_Installer.zip  # Distribution installer zip
├── installer/
│   ├── install.ps1             # Interactive installer (custom install path & shortcuts)
│   └── installer.iss           # Inno Setup wizard configuration
├── main.py                     # Application entry point (GUI + CLI)
├── config.py                   # Paths, API keys, ATS signatures
├── core/
│   ├── aggregator.py           # Concurrent multi-keyword & multi-source search
│   ├── ats_detector.py         # Workday, Personio, Greenhouse ATS classifier
│   ├── deduplicator.py         # Cross-platform job deduplication & keyword merging
│   ├── exporter.py             # Formatted Excel (.xlsx) generator with custom save dir
│   ├── models.py               # Data models
│   └── sources/                # API clients (Arbeitsagentur, Arbeitnow, JobSpy)
├── ui/
    ├── app.py                  # PyWebView window & API controller
    └── static/                 # HTML5/JS/CSS frontend with folder picker
```
