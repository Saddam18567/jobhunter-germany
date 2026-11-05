"""Export job listings to styled Excel (.xlsx) spreadsheets and UTF-8 CSV files."""

import datetime
import re
from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config import EXPORTS_DIR
from core.models import JobListing

def sanitize_filename(name: str) -> str:
    """Remove invalid characters for Windows/Linux filenames."""
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

class JobExporter:
    """Handles Excel and CSV exports with styling and direct links."""

    @staticmethod
    def generate_default_path(keyword: str, location: str, ext: str = "xlsx") -> Path:
        """Create a timestamped export filepath in exports/ directory."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_kw = sanitize_filename(keyword or "all_jobs")
        safe_loc = sanitize_filename(location or "germany")
        filename = f"jobs_germany_{safe_kw}_{safe_loc}_{ts}.{ext}"
        return EXPORTS_DIR / filename

    @staticmethod
    def to_dataframe(listings: List[JobListing]) -> pd.DataFrame:
        """Convert list of JobListing objects into a pandas DataFrame."""
        rows = []
        for job in listings:
            platforms_str = ", ".join(job.found_on) if job.found_on else job.source_platform
            tags_str = ", ".join(job.tags) if job.tags else ""
            rows.append({
                "Job Title": job.title,
                "Company": job.company,
                "Location": job.location,
                "Remote / Home Office": "Yes (Remote / Hybrid)" if job.is_remote else "On-Site",
                "Application Platform": job.application_platform,
                "Application Type": job.application_type,
                "How to Apply": job.how_to_apply,
                "Direct Apply Link": job.direct_apply_url or job.job_url,
                "Original Job URL": job.job_url,
                "Found On": platforms_str,
                "Date Posted": job.date_posted,
                "Job Type": job.job_type,
                "Salary": job.salary,
                "Skills & Tags": tags_str,
                "Description Snippet": job.description_snippet,
            })
        return pd.DataFrame(rows)

    @classmethod
    def export_csv(cls, listings: List[JobListing], output_path: Optional[Path | str] = None) -> str:
        """Export listings to CSV with UTF-8 BOM encoding for Excel compatibility."""
        if not output_path:
            kw = listings[0].title if listings else "search"
            loc = listings[0].city if listings else "de"
            output_path = cls.generate_default_path(kw, loc, "csv")
        
        path_obj = Path(output_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        df = cls.to_dataframe(listings)
        # Use utf-8-sig so German characters display seamlessly in Excel on Windows
        df.to_csv(path_obj, index=False, encoding="utf-8-sig")
        return str(path_obj.resolve())

    @classmethod
    def export_excel(cls, listings: List[JobListing], output_path: Optional[Path | str] = None) -> str:
        """Export listings to a styled Microsoft Excel (.xlsx) workbook with hyperlinks."""
        if not output_path:
            kw = listings[0].title if listings else "search"
            loc = listings[0].city if listings else "de"
            output_path = cls.generate_default_path(kw, loc, "xlsx")
        
        path_obj = Path(output_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        df = cls.to_dataframe(listings)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Jobs in Germany"
        ws.views.sheetView[0].showGridLines = True

        # Styles definition
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Navy Blue
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        link_font = Font(name="Segoe UI", size=10, color="2563EB", underline="single")
        zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        # Write Headers
        headers = list(df.columns)
        ws.append(headers)

        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
            cell.border = thin_border
        ws.row_dimensions[1].height = 28

        # Identify hyperlink columns
        direct_apply_col = headers.index("Direct Apply Link") + 1 if "Direct Apply Link" in headers else None
        job_url_col = headers.index("Original Job URL") + 1 if "Original Job URL" in headers else None

        # Write Data Rows
        for row_idx, row_data in enumerate(df.values, start=2):
            ws.append(list(row_data))
            ws.row_dimensions[row_idx].height = 22
            is_even = (row_idx % 2 == 0)

            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=row_idx, column=col_num)
                cell.font = regular_font
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")

                if is_even:
                    cell.fill = zebra_fill

                # Hyperlink formatting for URL columns
                if col_num in (direct_apply_col, job_url_col) and cell.value:
                    url_str = str(cell.value).strip()
                    if url_str.startswith("http://") or url_str.startswith("https://"):
                        label = "Apply Link ↗" if col_num == direct_apply_col else "View Listing ↗"
                        cell.hyperlink = url_str
                        cell.value = label
                        cell.font = link_font

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            # Set bounded width
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

        # Enable Excel Auto-Filter on header row
        ws.auto_filter.ref = ws.dimensions

        wb.save(path_obj)
        return str(path_obj.resolve())
