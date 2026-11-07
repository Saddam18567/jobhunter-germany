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
from typing import Dict, Any, List, Optional

import webview

try:
    import certifi
    ca_bundle = certifi.where()
    if ca_bundle and os.path.exists(ca_bundle):
        os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)
        os.environ.setdefault("CURL_CA_BUNDLE", ca_bundle)
except Exception:
    pass

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
        self.active_save_dir: str = self.get_default_save_dir()
        self.window = None

    def get_default_save_dir(self) -> str:
        """Default save location: user's Downloads or Exports folder."""
        user_downloads = Path.home() / "Downloads"
        if user_downloads.exists():
            return str(user_downloads.resolve())
        return str(EXPORTS_DIR.resolve())

    def select_save_directory(self) -> str:
        """Opens native OS folder picker to let user choose where Excel spreadsheets are saved."""
        try:
            target_win = self.window or (webview.windows[0] if webview.windows else None)
            if target_win:
                result = target_win.create_file_dialog(
                    webview.FOLDER_DIALOG,
                    directory=self.active_save_dir
                )
                if result and len(result) > 0:
                    chosen = result[0]
                    self.active_save_dir = chosen
                    return chosen
        except Exception as e:
            logger.warning(f"Native folder dialog error: {e}")

        return self.active_save_dir

    def search_jobs(self, filters_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Search jobs across German APIs and scrapers, and automatically generate Excel sheet."""
        try:
            kw = filters_dict.get("keyword", "")
            loc = filters_dict.get("location", "Deutschland")
            save_dir = filters_dict.get("save_directory") or self.active_save_dir
            if save_dir:
                self.active_save_dir = save_dir

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
                date_posted_days=int(filters_dict["date_posted_days"]) if filters_dict.get("date_posted_days") else None,
                save_directory=self.active_save_dir
            )

            self.current_jobs = self.aggregator.search(filters)
            stats = self.aggregator.calculate_stats(self.current_jobs)

            # Automatically generate Excel sheet in user's chosen folder
            excel_path = ""
            excel_filename = ""
            if self.current_jobs:
                default_path = JobExporter.generate_default_path(
                    self.last_keyword,
                    self.last_location,
                    "xlsx",
                    target_dir=self.active_save_dir
                )
                excel_path = JobExporter.export_excel(self.current_jobs, default_path)
                excel_filename = Path(excel_path).name
                self.last_excel_path = excel_path

            return {
                "success": True,
                "jobs": [j.to_dict() for j in self.current_jobs],
                "stats": stats,
                "excel_path": excel_path,
                "excel_filename": excel_filename,
                "save_directory": self.active_save_dir,
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
                "save_directory": self.active_save_dir,
                "download_url": ""
            }

    def export_excel_manual(self, custom_save_dir: str = "") -> str:
        """Export current jobs to Excel in specified directory and return file path."""
        if not self.current_jobs:
            raise ValueError("No job listings available to export.")

        target_dir = custom_save_dir or self.active_save_dir
        default_path = JobExporter.generate_default_path(self.last_keyword, self.last_location, "xlsx", target_dir=target_dir)
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

    def open_exports_folder(self, folder_override: str = "") -> str:
        """Open the save folder in Windows Explorer, macOS Finder, or Linux file manager."""
        folder_path = folder_override or self.active_save_dir or str(EXPORTS_DIR.resolve())
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

        elif self.path == "/api/select_folder":
            chosen = self.api.select_save_directory()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "path": chosen}).encode("utf-8"))

        elif self.path == "/api/get_save_dir":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "path": self.api.active_save_dir}).encode("utf-8"))

        elif self.path == "/api/export_excel":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            data = json.loads(body) if body else {}
            custom_dir = data.get("save_directory", "")

            try:
                filepath = self.api.export_excel_manual(custom_dir)
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
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            data = json.loads(body) if body else {}
            folder = data.get("path", "")
            path = self.api.open_exports_folder(folder)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "path": path}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        if self.path.startswith("/download/"):
            filename = self.path[len("/download/"):]
            # Look in active save dir or EXPORTS_DIR
            filepath = Path(self.api.active_save_dir) / filename
            if not filepath.exists():
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


def start_http_server(host: str = "127.0.0.1", port: int = 5892) -> tuple[HTTPServer, int]:
    """Start local background HTTP server, auto-incrementing port if already in use."""
    server = None
    target_port = port
    
    # Try preferred port and subsequent ports in case previous instance is running
    for p in range(port, port + 25):
        try:
            server = HTTPServer((host, p), AppRequestHandler)
            target_port = p
            break
        except OSError:
            continue

    if server is None:
        # Fallback to dynamic OS port allocation
        server = HTTPServer((host, 0), AppRequestHandler)
        target_port = server.server_port

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, target_port


def run_desktop_app(force_browser: bool = False, host: str = "127.0.0.1", port: int = 5892):
    """
    Launch JobHunter Germany desktop app.
    Uses PyWebView native desktop window when available (e.g. on Windows with WebView2),
    or falls back gracefully to opening the user's default browser or serving over HTTP.
    """
    # Configure pythonnet runtime path on Windows if frozen
    if platform.system() == "Windows" and getattr(sys, "frozen", False):
        try:
            base_dir = Path(sys.executable).resolve().parent
            candidates = [
                base_dir / "python312.dll",
                base_dir / "_internal" / "python312.dll",
                base_dir / f"python{sys.version_info.major}{sys.version_info.minor}.dll",
                base_dir / "_internal" / f"python{sys.version_info.major}{sys.version_info.minor}.dll",
            ]
            for cand in candidates:
                if cand.exists():
                    os.environ.setdefault("PYTHONNET_PYDLL", str(cand))
                    break
        except Exception:
            pass

    api = AppRequestHandler.api
    server, actual_port = start_http_server(host=host, port=port)
    url = f"http://127.0.0.1:{actual_port}/"

    can_open_webview = (not force_browser) and (webview.guilib is not None or platform.system() in ["Windows", "Darwin"])

    if can_open_webview:
        try:
            logger.info("Initializing native desktop window...")
            window = webview.create_window(
                title="JobHunter Germany - AI & ATS Job Finder",
                url=url,
                js_api=api,
                width=1280,
                height=860,
                min_size=(960, 640),
                confirm_close=False,
            )
            api.window = window
            webview.start(debug=False)
            return
        except Exception as e:
            logger.warning(f"Native window could not be initialized ({e}). Falling back to browser interface...")

    # Fallback: Launch default browser
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning(f"Could not open browser automatically: {e}")

    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
