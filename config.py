"""Configuration settings and constants for JobHunter Germany."""

import sys
from pathlib import Path

# Base Paths (handles standalone PyInstaller frozen app or normal python script)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "ui" / "static"
# If running frozen and static is inside _internal/ui/static
if not STATIC_DIR.exists() and (BASE_DIR / "_internal" / "ui" / "static").exists():
    STATIC_DIR = BASE_DIR / "_internal" / "ui" / "static"

EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Bundesagentur für Arbeit (BA) REST API Configuration
BA_API_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
BA_API_KEY = "jobboerse-jobsuche"
BA_JOB_DETAIL_URL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{refnr}"

# Arbeitnow German Jobs REST API
ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"

# Default Search Filters
DEFAULT_LOCATION = "Deutschland"
DEFAULT_DISTANCE = 50  # km
DEFAULT_RESULTS_PER_SOURCE = 25
DEFAULT_SOURCES = ["arbeitsagentur", "indeed", "linkedin", "arbeitnow", "glassdoor"]

# Major German Cities for Quick Suggestions
GERMAN_CITIES = [
    "Deutschland (Ganzes Land)",
    "Berlin",
    "München",
    "Hamburg",
    "Frankfurt am Main",
    "Köln",
    "Stuttgart",
    "Düsseldorf",
    "Leipzig",
    "Dortmund",
    "Essen",
    "Bremen",
    "Dresden",
    "Hannover",
    "Nürnberg",
]

# ATS (Applicant Tracking System) Regex Signatures and Platform Names
ATS_DETECTION_PATTERNS = [
    {
        "name": "Workday",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*(?:myworkdayjobs\.com|workday\.com)/[^\s\"'<>]+",
        "category": "Enterprise ATS",
        "instructions": "Apply directly on company Workday ATS portal (Direct review, skips aggregator queue).",
    },
    {
        "name": "Personio",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*(?:jobs\.personio\.de|personio\.de/job|personio\.net)/[^\s\"'<>]+",
        "category": "European / German ATS",
        "instructions": "Apply directly via Personio ATS portal (Leading German recruitment system).",
    },
    {
        "name": "Greenhouse",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*(?:boards\.greenhouse\.io|job-boards\.greenhouse\.io|boards\.eu\.greenhouse\.io|grnh\.se)/[^\s\"'<>]+",
        "category": "Modern Tech ATS",
        "instructions": "Apply directly on company Greenhouse job board.",
    },
    {
        "name": "Lever",
        "pattern": r"(?:https?://)?jobs\.lever\.co/[^\s\"'<>]+",
        "category": "Modern Tech ATS",
        "instructions": "Apply directly on company Lever application page.",
    },
    {
        "name": "Softgarden",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*(?:softgarden\.io|softgarden\.de|jobbase\.io)/[^\s\"'<>]+",
        "category": "German Enterprise ATS",
        "instructions": "Apply directly on company Softgarden candidate portal.",
    },
    {
        "name": "SmartRecruiters",
        "pattern": r"(?:https?://)?(?:jobs\.smartrecruiters\.com|smrtr\.io)/[^\s\"'<>]+",
        "category": "Enterprise ATS",
        "instructions": "Apply directly on SmartRecruiters portal.",
    },
    {
        "name": "Ashby",
        "pattern": r"(?:https?://)?jobs\.ashbyhq\.com/[^\s\"'<>]+",
        "category": "High-Growth Tech ATS",
        "instructions": "Apply directly on Ashby application form.",
    },
    {
        "name": "JOIN Solutions",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*join\.com/(?:companies|jobs)/[^\s\"'<>]+",
        "category": "German / EU Startup ATS",
        "instructions": "Apply directly via JOIN job board.",
    },
    {
        "name": "Teamtailor",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*teamtailor\.com/[^\s\"'<>]+",
        "category": "Modern ATS",
        "instructions": "Apply directly on Teamtailor career site.",
    },
    {
        "name": "Recruitee",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*recruitee\.com/[^\s\"'<>]+",
        "category": "Collaborative ATS",
        "instructions": "Apply directly on Recruitee career portal.",
    },
    {
        "name": "Taleo (Oracle)",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*taleo\.net/[^\s\"'<>]+",
        "category": "Enterprise ATS",
        "instructions": "Apply directly on Oracle Taleo enterprise portal.",
    },
    {
        "name": "SAP SuccessFactors",
        "pattern": r"(?:https?://)?(?:[a-zA-Z0-9_\-]+\.)*successfactors\.(?:eu|com)/[^\s\"'<>]+",
        "category": "Enterprise ATS",
        "instructions": "Apply directly on company SAP SuccessFactors career portal.",
    },
    {
        "name": "Workable",
        "pattern": r"(?:https?://)?apply\.workable\.com/[^\s\"'<>]+",
        "category": "Modern ATS",
        "instructions": "Apply directly via Workable job application.",
    },
    {
        "name": "Bundesagentur für Arbeit",
        "pattern": r"(?:https?://)?(?:www\.)?arbeitsagentur\.de/jobsuche/jobdetail/[^\s\"'<>]+",
        "category": "Official German Government Portal",
        "instructions": "Apply or contact employer directly via official Bundesagentur Jobbörse portal.",
    },
]
