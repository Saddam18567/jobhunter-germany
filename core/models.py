"""Data models for JobHunter Germany."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import hashlib
import re

@dataclass
class SearchFilters:
    keyword: str  # Can contain multiple comma/semicolon-separated keywords
    location: str = "Deutschland"
    distance: int = 50  # km
    is_remote: bool = False
    job_type: Optional[str] = None  # "fulltime", "parttime", "contract", "internship", None
    results_per_source: int = 25
    sources: List[str] = field(default_factory=lambda: ["arbeitsagentur", "indeed", "linkedin", "arbeitnow", "glassdoor"])
    date_posted_days: Optional[int] = None
    save_directory: Optional[str] = None  # User-defined folder to save Excel spreadsheets

    @property
    def keywords_list(self) -> List[str]:
        """Parse multiple keywords separated by commas, semicolons, or newlines."""
        if not self.keyword:
            return []
        parts = re.split(r"[,;\n|]+", self.keyword)
        cleaned = [p.strip() for p in parts if p.strip()]
        return cleaned if cleaned else [self.keyword.strip()]

@dataclass
class JobListing:
    id: str
    title: str
    company: str
    location: str
    city: str = ""
    country: str = "Germany"
    source_platform: str = ""
    found_on: List[str] = field(default_factory=list)
    job_url: str = ""
    direct_apply_url: str = ""
    application_platform: str = "Unknown"
    application_type: str = "Aggregator"
    how_to_apply: str = ""
    is_remote: bool = False
    job_type: str = "Full-time"
    date_posted: str = ""
    salary: str = "Not specified"
    description_snippet: str = ""
    tags: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)  # Which user keyword(s) matched this job

    @classmethod
    def generate_id(cls, title: str, company: str, location: str) -> str:
        """Create a deterministic hash ID from core fields."""
        raw = f"{title.strip().lower()}|{company.strip().lower()}|{location.strip().lower()}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        data = asdict(self)
        return data
