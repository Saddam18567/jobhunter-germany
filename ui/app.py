"""Desktop Window Controller & Local HTTP Server Bridge for JobHunter Germany."""

import os
import sys
import json
import logging
import platform
import subprocess
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Any, List

import webview

from config import STATIC_DIR, EXPORTS_DIR
from core.models import SearchFilters, JobListing
from core.aggregator import JobAggregator
from core.exporter import JobExporter

logger = logging.getLogger(__name__)

class JobHunterAPI:
    """Python API exposed to the JavaScript frontend via PyWebView."""

    def __init__(self):
        self.aggregator = JobAggregator()
        self.current_jobs: List[JobListing] = []
        self.last_keyword: str = "jobs"
        self.last_location: str = "germany"
        self.last_excel_path: str = ""

    def search_jobs(self, filters_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Search jobs across German APIs and scrapers, and automatically generate Excel sheet."""
        try:
            kw = filters_dict.get("keyword", "")
            loc = filters_dict.get("location", "Deutschland")
            self.last_keyword = kw
            self.last_location = loc

            filters = SearchFilters(
                keyword=kw,
                location=loc,
                distance=int(filters_dict.get("distance", 50)),
                is_remote=bool(filters_dict.get("is_remote", False)),
                job_type=filters_dict.get("job_type") or None,
                results_per_source=int(filters_dict.get("results_per_source", 25)),
                sources=filters_dict.get("sources", ["arbeitsagentur", "indeed", "linkedin"]),
                date_posted_days=int(filters_dict["date_posted_days"]) if filters_dict.get("date_posted_days") else None
            )

            self.current_jobs = self.aggregator.search(filters)
            stats = self.aggregator.calculate_stats(self.current_jobs)

            # Automatically generate Excel sheet upon search completion
            excel_path = ""
            excel_filename = ""
            if self.current_jobs:
                default_path = JobExporter.generate_default_path(self.last_keyword, self.last_location, "xlsx")
                excel_path = JobExporter.export_excel(self.current_jobs, default_path)
                excel_filename = Path(excel_path).name
                self.last_excel_path = excel_path

            return {
                "success": True,
                "jobs": [j.to_dict() for j in self.current_jobs],
                "stats": stats,
                "excel_path": excel_path,
                "excel_filename": excel_filename,
                "download_url": f"/download/{excel_filename}" if excel_filename else ""
            }
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "jobs": [],
                "stats": {},
                "excel_path": "",
                "excel_filename": "",
                "download_url": ""
            }

    def export_excel_manual(self) -> str:
        """Export current jobs to Excel and return absolute file path."""
        if not self.current_jobs:
            raise ValueError("No job listings available to export.")

        default_path = JobExporter.generate_default_path(self.last_keyword, self.last_location, "xlsx")
        path = JobExporter.export_excel(self.current_jobs, default_path)
        self.last_excel_path = path
        return path

    def open_excel_file(self, file_path: str = "") -> str:
        """Open an Excel file directly in Microsoft Excel or system default spreadsheet viewer."""
        target = file_path or self.last_excel_path
        if not target or not Path(target).exists():
            raise FileNotFoundError("Excel file not found.")

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(target)
            elif system == "Darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
            return target
        except Exception as e:
            logger.warning(f"Could not open file automatically: {e}")
            return target

    def open_in_browser(self, url: str):
        """Open a job URL in the user's default desktop web browser."""
        if url:
            webbrowser.open(url)

    def open_exports_folder(self) -> str:
        """Open the exports folder in Windows Explorer, macOS Finder, or Linux file manager."""
        folder_path = str(EXPORTS_DIR.resolve())
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(folder_path)
            elif system == "Darwin":
                subprocess.Popen(["open", folder_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
            return folder_path
        except Exception as e:
            logger.warning(f"Could not open directory natively: {e}")
            return folder_path


class AppRequestHandler(SimpleHTTPRequestHandler):
    """Local HTTP Server Handler for browser fallback and file downloads."""

    api = JobHunterAPI()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/search":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            filters_dict = json.loads(body)
            result = self.api.search_jobs(filters_dict)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))

        elif self.path == "/api/export_excel":
            try:
                filepath = self.api.export_excel_manual()
                filename = Path(filepath).name
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "path": filepath,
                    "filename": filename,
                    "download_url": f"/download/{filename}"
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif self.path == "/api/open_file":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body) if body else {}
            path = data.get("path", "")
            try:
                opened_path = self.api.open_excel_file(path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "path": opened_path}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif self.path == "/api/open_folder":
            path = self.api.open_exports_folder()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "path": path}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        if self.path.startswith("/download/"):
            filename = self.path[len("/download/"):]
            filepath = EXPORTS_DIR / filename
            if filepath.exists() and filepath.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(filepath.stat().st_size))
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File not found")
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass


def start_http_server(port: int = 5892) -> HTTPServer:
    """Start local background HTTP server."""
    server = HTTPServer(("127.0.0.1", port), AppRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def run_desktop_app(force_browser: bool = False, port: int = 5892):
    """
    Launch JobHunter Germany desktop app.
    Uses PyWebView native desktop window when available (e.g. on Windows with WebView2),
    or falls back gracefully to opening the user's default browser.
    """
    api = AppRequestHandler.api
    start_http_server(port=port)
    url = f"http://127.0.0.1:{port}/"

    can_open_webview = (not force_browser) and (webview.guilib is not None or platform.system() in ["Windows", "Darwin"])

    if can_open_webview:
        try:
            print("[INFO] Launching JobHunter Germany in native desktop window...")
            window = webview.create_window(
                title="JobHunter Germany 🇩🇪 - AI & ATS Job Finder",
                url=url,
                js_api=api,
                width=1280,
                height=840,
                min_size=(960, 640),
                confirm_close=False,
            )
            webview.start(debug=False)
            return
        except Exception as e:
            print(f"[WARNING] Native window could not be initialized ({e}). Falling back to browser interface...")

    print(f"\n=======================================================")
    print(f"  🇩🇪 JobHunter Germany is running!")
    print(f"  URL: {url}")
    print(f"  Press Ctrl+C in this terminal to stop the application.")
    print(f"=======================================================\n")
    webbrowser.open(url)
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] JobHunter Germany shutting down.")
