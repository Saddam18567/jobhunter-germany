#!/usr/bin/env python3
"""
JobHunter Germany - Entry Point
Unified Job Search across German APIs, Scrapers (JobSpy), and ATS Detection.
"""

import os
import sys
import argparse
from pathlib import Path

# Fix Windows console encoding and attach to console if run from CLI/terminal
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.AttachConsole(-1)
        if sys.stdout is None or not hasattr(sys.stdout, "write"):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8")
        if sys.stderr is None or not hasattr(sys.stderr, "write"):
            sys.stderr = open("CONOUT$", "w", encoding="utf-8")
    except Exception:
        pass
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Configure pythonnet DLL and CA Certs globally for frozen PyInstaller environment
if sys.platform == "win32" and getattr(sys, "frozen", False):
    try:
        base_dir = Path(sys.executable).resolve().parent
        for cand in [
            base_dir / "python312.dll",
            base_dir / "_internal" / "python312.dll",
            base_dir / f"python{sys.version_info.major}{sys.version_info.minor}.dll",
            base_dir / "_internal" / f"python{sys.version_info.major}{sys.version_info.minor}.dll",
        ]:
            if cand.exists():
                os.environ.setdefault("PYTHONNET_PYDLL", str(cand))
                break
    except Exception:
        pass

try:
    import certifi
    ca_bundle = certifi.where()
    if ca_bundle and os.path.exists(ca_bundle):
        os.environ.setdefault("SSL_CERT_FILE", ca_bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_bundle)
        os.environ.setdefault("CURL_CA_BUNDLE", ca_bundle)
except Exception:
    pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.app import run_desktop_app
from core.models import SearchFilters
from core.aggregator import JobAggregator
from core.exporter import JobExporter

def run_cli_mode(args):
    """Run job search directly from terminal and export results."""
    print("=======================================================")
    print("       JobHunter Germany - CLI Mode [DE]")
    print("=======================================================")
    print(f"Keyword:      {args.keyword}")
    print(f"Location:     {args.location}")
    print(f"Radius:       {args.distance} km")
    print(f"Remote Only:  {args.remote}")
    print(f"Sources:      {', '.join(args.sources)}")
    print("-------------------------------------------------------")

    filters = SearchFilters(
        keyword=args.keyword,
        location=args.location,
        distance=args.distance,
        is_remote=args.remote,
        job_type=args.type,
        results_per_source=args.limit,
        sources=args.sources,
        date_posted_days=args.days
    )

    aggregator = JobAggregator()
    
    def on_progress(msg):
        print(f"[*] {msg}")

    jobs = aggregator.search(filters, progress_callback=on_progress)
    stats = aggregator.calculate_stats(jobs)

    print("-------------------------------------------------------")
    print(f"Found {len(jobs)} unique jobs in Germany!")
    print(f"Direct ATS listings (Workday, Personio, etc.): {stats.get('direct_ats_jobs')}")
    print(f"Remote positions:                              {stats.get('remote_jobs')}")
    print("-------------------------------------------------------")

    if args.export:
        saved = JobExporter.export_excel(jobs, args.export)
        print(f"[+] Results exported to: {saved}")
    else:
        # Default export to Excel
        xlsx_file = JobExporter.export_excel(jobs)
        print(f"[+] Excel (.xlsx) generated: {xlsx_file}")

def run_internal_smoke_test(host: str = "127.0.0.1", port: int = 5892) -> bool:
    """Run an automated internal self-test of the binary, static assets, and API server."""
    import urllib.request
    import json
    from config import STATIC_DIR, EXPORTS_DIR
    from ui.app import start_http_server

    print("=======================================================")
    print("      JobHunter Germany - Internal Smoke Test          ")
    print("=======================================================")
    print(f"Static Directory:  {STATIC_DIR}")
    print(f"Exports Directory: {EXPORTS_DIR}")

    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        print(f"[FAIL] index.html not found in {STATIC_DIR}")
        return False
    print("[+] Static UI assets verified.")

    try:
        server, actual_port = start_http_server(host=host, port=port)
        print(f"[+] Local HTTP server started on http://{host}:{actual_port}/")

        # 1. Test GET /
        req_url = f"http://{host}:{actual_port}/"
        with urllib.request.urlopen(req_url, timeout=5) as response:
            content = response.read().decode("utf-8")
            if response.status != 200 or "JobHunter" not in content:
                print(f"[FAIL] Unexpected HTTP response: status {response.status}")
                return False
        print("[+] HTTP GET / served 200 OK with UI HTML.")

        # 2. Test POST /api/get_save_dir
        post_url = f"http://{host}:{actual_port}/api/get_save_dir"
        post_req = urllib.request.Request(
            post_url,
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(post_req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if not data.get("success"):
                print(f"[FAIL] API /api/get_save_dir failed: {data}")
                return False
        print(f"[+] API backend operational. Active save directory: {data.get('path')}")

        server.shutdown()
        print("-------------------------------------------------------")
        print("[+] ALL INTERNAL SMOKE TESTS PASSED SUCCESSFULLY!")
        print("=======================================================")
        return True
    except Exception as e:
        print(f"[FAIL] Smoke test encountered an exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description="JobHunter Germany - AI & ATS Job Finder for Germany (Bundesagentur API + JobSpy + Workday/Personio Detector)"
    )
    parser.add_argument("--cli", action="store_true", help="Run in headless CLI mode instead of GUI")
    parser.add_argument("--test", action="store_true", help="Run internal smoke test of assets and HTTP server, then exit")
    parser.add_argument("--browser", action="store_true", help="Force browser window instead of native desktop window")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind HTTP server to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5892, help="Port for the local backend server (default: 5892)")

    # CLI Search Arguments
    parser.add_argument("-k", "--keyword", type=str, default="Python Developer", help="Job keyword or title")
    parser.add_argument("-l", "--location", type=str, default="Deutschland", help="Location in Germany")
    parser.add_argument("-d", "--distance", type=int, default=50, help="Search radius in km")
    parser.add_argument("-r", "--remote", action="store_true", help="Only remote / home-office jobs")
    parser.add_argument("-t", "--type", type=str, choices=["fulltime", "parttime", "contract"], help="Employment type")
    parser.add_argument("--days", type=int, default=None, help="Published in last N days")
    parser.add_argument("--limit", type=int, default=25, help="Results limit per source")
    parser.add_argument(
        "-s", "--sources", nargs="+",
        default=["arbeitsagentur", "indeed", "linkedin", "arbeitnow", "glassdoor"],
        help="Sources: arbeitsagentur, indeed, linkedin, arbeitnow, glassdoor, google"
    )
    parser.add_argument("-e", "--export", type=str, default=None, help="Custom export filepath (.xlsx or .csv)")

    args = parser.parse_args()

    if args.test:
        success = run_internal_smoke_test(host=args.host, port=args.port)
        sys.exit(0 if success else 1)
    elif args.cli:
        run_cli_mode(args)
    else:
        run_desktop_app(force_browser=args.browser, host=args.host, port=args.port)

if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            sys.exit(getattr(e, "code", 0) or 0)

        import time, traceback
        err_msg = traceback.format_exc()
        try:
            from config import EXPORTS_DIR
            crash_file = EXPORTS_DIR / "crash.log"
        except Exception:
            crash_file = Path(os.environ.get("LOCALAPPDATA", ".")) / "JobHunterGermany" / "crash.log"
        try:
            crash_file.parent.mkdir(parents=True, exist_ok=True)
            with open(crash_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- CRASH AT {time.ctime()} ---\n{err_msg}\n")
        except Exception:
            pass

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"JobHunter Germany encountered an issue during startup:\n\n{str(e)[:400]}\n\nLog saved to:\n{crash_file}",
                    "JobHunter Germany Error",
                    0x10  # MB_ICONERROR
                )
            except Exception:
                pass
        sys.exit(1)
