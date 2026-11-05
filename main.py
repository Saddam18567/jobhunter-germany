#!/usr/bin/env python3
"""
JobHunter Germany - Entry Point
Unified Job Search across German APIs, Scrapers (JobSpy), and ATS Detection.
"""

import sys
import argparse
from pathlib import Path

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
    print("       JobHunter Germany - CLI Mode 🇩🇪")
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

def main():
    parser = argparse.ArgumentParser(
        description="JobHunter Germany - AI & ATS Job Finder for Germany (Bundesagentur API + JobSpy + Workday/Personio Detector)"
    )
    parser.add_argument("--cli", action="store_true", help="Run in headless CLI mode instead of GUI")
    parser.add_argument("--browser", action="store_true", help="Force browser window instead of native desktop window")
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

    if args.cli:
        run_cli_mode(args)
    else:
        run_desktop_app(force_browser=args.browser, port=args.port)

if __name__ == "__main__":
    main()
