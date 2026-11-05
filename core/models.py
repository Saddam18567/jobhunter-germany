"""Data models for JobHunter Germany."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import hashlib

@dataclass
class SearchFilters:
    keyword: str
    location: str = "Deutschland"
    distance: int = 50  # km
    is_remote: bool = False
    job_type: Optional[str] = None  # "fulltime", "parttime", "contract", "internship", None
    results_per_source: int = 25
    sources: List[str] = field(default_factory=lambda: ["arbeitsagentur", "indeed", "linkedin", "arbeitnow", "glassdoor"])
    date_posted_days: Optional[int] = None  # None = any, 1 = past 24h, 7 = past week, etc.

@dataclass
class JobListing:
    id: str
    title: str
    company: str
    location: str
    city: str = ""
    country: str = "Germany"
    source_platform: str = ""  # Initial source (e.g. "Bundesagentur für Arbeit")
    found_on: List[str] = field(default_factory=list)  # All sources found on
    job_url: str = ""  # Primary link
    direct_apply_url: str = ""  # Direct ATS link if detected
    application_platform: str = "Unknown"  # E.g. "Workday", "Personio", "Bundesagentur", "LinkedIn"
    application_type: str = "Aggregator"  # "Direct ATS", "Government Portal", "Job Board"
    how_to_apply: str = ""  # Plain English/German instruction on applying
    is_remote: bool = False
    job_type: str = "Full-time"
    date_posted: str = ""
    salary: str = "Not specified"
    description_snippet: str = ""
    tags: List[str] = field(default_factory=list)

    @classmethod
    def generate_id(cls, title: str, company: str, location: str) -> str:
        """Create a deterministic hash ID from core fields."""
        raw = f"{title.strip().lower()}|{company.strip().lower()}|{location.strip().lower()}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        data = asdict(self)
        return data
