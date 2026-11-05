"""ATS (Applicant Tracking System) detection, link resolution, and application guidance."""

import re
import urllib.parse
from typing import Tuple, Optional
import requests
from config import ATS_DETECTION_PATTERNS

# Additional regex patterns to discover candidate application URLs in raw HTML or descriptions
URL_REGEX = re.compile(r'https?://[^\s<>"\')]+', re.IGNORECASE)

class ATSDetector:
    """Detects ATS systems and formulates application guidance."""

    @staticmethod
    def detect_ats_from_url(url: str) -> Optional[dict]:
        """Check if a URL matches known ATS domains."""
        if not url:
            return None
        for pattern_info in ATS_DETECTION_PATTERNS:
            if re.search(pattern_info["pattern"], url, re.IGNORECASE):
                return pattern_info
        return None

    @staticmethod
    def extract_ats_link_from_text(text: str) -> Tuple[Optional[str], Optional[dict]]:
        """Search text / description for embedded ATS application links."""
        if not text:
            return None, None
        
        found_urls = URL_REGEX.findall(text)
        for u in found_urls:
            # Clean trailing punctuation
            u_clean = u.rstrip(".,;:!?)")
            matched = ATSDetector.detect_ats_from_url(u_clean)
            if matched:
                return u_clean, matched
        return None, None

    @staticmethod
    def resolve_application_details(
        source_platform: str,
        job_url: str,
        direct_url: Optional[str] = None,
        description: str = "",
        easy_apply: bool = False
    ) -> Tuple[str, str, str, str]:
        """
        Determines:
        1. application_platform (e.g. Workday, Personio, LinkedIn Easy Apply)
        2. application_type (e.g. Direct ATS, Government Portal, Aggregator)
        3. how_to_apply (Actionable human-readable instructions)
        4. direct_apply_url (The best URL to use for applying)
        """
        best_url = direct_url if (direct_url and direct_url != job_url) else job_url

        # 1. Check if direct_url matches an ATS
        ats_info = ATSDetector.detect_ats_from_url(best_url)
        
        # 2. Check if primary job_url matches an ATS
        if not ats_info and job_url:
            ats_info = ATSDetector.detect_ats_from_url(job_url)
            if ats_info:
                best_url = job_url

        # 3. Check if description has an embedded ATS link (e.g. from Workday, Greenhouse, Personio)
        if not ats_info and description:
            embedded_url, embedded_ats = ATSDetector.extract_ats_link_from_text(description)
            if embedded_ats and embedded_url:
                best_url = embedded_url
                ats_info = embedded_ats

        # 4. If ATS matched:
        if ats_info:
            platform_name = ats_info["name"]
            app_type = "Direct ATS" if platform_name != "Bundesagentur für Arbeit" else "Government Portal"
            how_to_apply = f"{ats_info['instructions']} Open link directly to submit your CV."
            return platform_name, app_type, how_to_apply, best_url

        # 5. Bundesagentur für Arbeit specific handling
        if "arbeitsagentur" in source_platform.lower() or "arbeitsagentur.de" in (job_url or ""):
            return (
                "Bundesagentur für Arbeit",
                "Government Portal",
                "Apply via official Bundesagentur portal or contact employer directly using the reference number.",
                best_url or job_url
            )

        # 6. Arbeitnow handling
        if "arbeitnow" in source_platform.lower():
            return (
                "Arbeitnow Direct",
                "Job Board / Direct",
                "Apply directly on the employer listing or company site via Arbeitnow.",
                best_url or job_url
            )

        # 7. LinkedIn / Indeed / Glassdoor handling
        if "linkedin" in source_platform.lower():
            if easy_apply:
                return (
                    "LinkedIn Easy Apply",
                    "Aggregator 1-Click",
                    "Apply instantly via LinkedIn 1-Click Easy Apply.",
                    best_url or job_url
                )
            return (
                "LinkedIn",
                "Job Board",
                "Apply on company website or via LinkedIn job listing.",
                best_url or job_url
            )

        if "indeed" in source_platform.lower():
            if easy_apply:
                return (
                    "Indeed Apply",
                    "Aggregator 1-Click",
                    "Apply directly via Indeed Instant Application.",
                    best_url or job_url
                )
            return (
                "Indeed Germany",
                "Job Board",
                "Apply on employer career site or via Indeed.",
                best_url or job_url
            )

        if "glassdoor" in source_platform.lower():
            return (
                "Glassdoor",
                "Job Board",
                "Apply via Glassdoor employer posting.",
                best_url or job_url
            )

        # Fallback
        return (
            source_platform or "Direct Company",
            "Company Career Portal",
            "Visit the provided job link to review requirements and apply directly.",
            best_url or job_url
        )
