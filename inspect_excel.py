#!/usr/bin/env python3
"""
Inspect the latest generated Excel file in terminal.
Useful when connecting via SSH without a graphical desktop.
"""

import sys
import glob
from pathlib import Path
import openpyxl

def main():
    exports_dir = Path(__file__).resolve().parent / "exports"
    
    # Check custom arg or search exports/
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        files = sorted(exports_dir.glob("*.xlsx"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            print("[!] No Excel files found in exports/ directory yet.")
            print("Run a search first: python3 main.py --cli -k 'Python Developer, DevOps' -l 'Berlin'")
            return
        target_path = files[0]

    print("=========================================================================================")
    print(f"[*] Viewing Excel File: {target_path.name}")
    print(f"[*] Full Path:         {target_path.resolve()}")
    print("=========================================================================================\n")

    wb = openpyxl.load_workbook(target_path)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]
    total_rows = ws.max_row - 1

    print(f"Total Jobs in Workbook: {total_rows}\n")

    # Column indices
    title_idx = headers.index("Job Title")
    comp_idx = headers.index("Company")
    loc_idx = headers.index("Location")
    kw_idx = headers.index("Matched Keywords") if "Matched Keywords" in headers else None
    platform_idx = headers.index("Application Platform")
    type_idx = headers.index("Application Type")
    apply_col = headers.index("Direct Apply Link")
    how_idx = headers.index("How to Apply")

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=1):
        vals = [c.value for c in row]
        title = vals[title_idx]
        company = vals[comp_idx]
        loc = vals[loc_idx]
        platform = vals[platform_idx]
        app_type = vals[type_idx]
        how_to = vals[how_idx]
        kw = vals[kw_idx] if kw_idx is not None else ""

        # Hyperlink resolution
        apply_cell = row[apply_col]
        apply_url = apply_cell.hyperlink.target if apply_cell.hyperlink else str(apply_cell.value)

        ats_badge = f"[DIRECT ATS: {platform}]" if app_type == "Direct ATS" else f"[{platform}]"

        print(f"#{idx}. {title}")
        print(f"    Company:     {company}")
        print(f"    Location:    {loc}")
        if kw:
            print(f"    Keywords:    {kw}")
        print(f"    Platform:    {ats_badge} ({app_type})")
        print(f"    Guidance:    {how_to}")
        print(f"    Direct Link: {apply_url}")
        print("    " + "-" * 75)

    print("\n=========================================================================================")
    print("[+] All jobs listed above are stored in the Excel (.xlsx) sheet.")
    print("=========================================================================================\n")

if __name__ == "__main__":
    main()
