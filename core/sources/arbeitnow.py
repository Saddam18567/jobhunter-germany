"""Arbeitnow REST API Client - German Tech & Direct Jobs."""

import logging
import datetime
import requests
import certifi
from bs4 import BeautifulSoup
from typing import List, Callable, Optional
from config import ARBEITNOW_API_URL
from core.models import SearchFilters, JobListing
from core.sources.base import BaseJobSource
from core.ats_detector import ATSDetector

logger = logging.getLogger(__name__)

class ArbeitnowSource(BaseJobSource):
    """Client for Arbeitnow German Job Board API."""

    def __init__(self):
        super().__init__("Arbeitnow")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def search(
        self,
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        results: List[JobListing] = []
        if progress_callback:
            progress_callback(f"Querying Arbeitnow API for '{filters.keyword}' in Germany...")

        target_kw = filters.keyword.lower().strip()
        kw_terms = [t.strip() for t in target_kw.split() if len(t.strip()) > 1]
        
        raw_loc = (filters.location or "").lower().strip()
        target_loc = raw_loc.split(",")[0].strip()
        is_all_germany = target_loc in ["deutschland", "deutschland (ganzes land)", "germany", "all", ""]

        try:
            ca_bundle = certifi.where()
            # Fetch up to 2 pages (up to 600 listings) to filter relevant jobs
            page_count = 2
            collected_raw = []
            
            for page in range(1, page_count + 1):
                url = f"{ARBEITNOW_API_URL}?page={page}"
                resp = requests.get(url, headers=self.headers, timeout=12, verify=ca_bundle)
                if resp.status_code == 200:
                    data = resp.json()
                    jobs_chunk = data.get("data", [])
                    collected_raw.extend(jobs_chunk)
                    if not jobs_chunk:
                        break
                else:
                    break

            if progress_callback:
                progress_callback(f"Scanning {len(collected_raw)} Arbeitnow listings for matches...")

            for item in collected_raw:
                title = item.get("title") or ""
                company = item.get("company_name") or "Employer"
                location = item.get("location") or "Germany"
                tags = item.get("tags") or []
                raw_desc = item.get("description") or ""

                # Strip HTML from description for snippet and link detection
                soup = BeautifulSoup(raw_desc, "html.parser")
                clean_text = soup.get_text(separator=" ", strip=True)

                title_lower = title.lower()
                tags_lower = " ".join(tags).lower()
                desc_lower = clean_text.lower()
                searchable_corpus = f"{title_lower} {tags_lower} {desc_lower}"

                # Match keyword terms flexibly across full description
                matched_kw = False
                if target_kw in searchable_corpus:
                    matched_kw = True
                elif kw_terms and all(term in searchable_corpus for term in kw_terms):
                    matched_kw = True
                elif kw_terms and any(term in title_lower or term in tags_lower for term in kw_terms):
                    matched_kw = True

                if not matched_kw:
                    continue

                # Remote status detection
                is_remote = (
                    bool(item.get("remote", False)) or
                    "remote" in location.lower() or
                    "remote" in title_lower or
                    "home office" in desc_lower or
                    "homeoffice" in desc_lower or
                    "mobiles arbeiten" in desc_lower
                )

                # Match remote filter
                if filters.is_remote and not is_remote:
                    continue

                # Match location
                if not is_all_germany and target_loc:
                    if target_loc not in location.lower() and not (filters.is_remote and is_remote):
                        continue

                # Format date
                created_at = item.get("created_at")
                date_str = ""
                if isinstance(created_at, (int, float)):
                    date_str = datetime.datetime.fromtimestamp(created_at).strftime("%Y-%m-%d")
                elif isinstance(created_at, str):
                    date_str = created_at[:10]

                # Determine ATS and direct application links
                job_url = item.get("url") or ""
                app_platform, app_type, how_to_apply, direct_apply_url = ATSDetector.resolve_application_details(
                    source_platform="Arbeitnow",
                    job_url=job_url,
                    description=raw_desc
                )

                job_types = item.get("job_types") or []
                job_type_str = ", ".join(job_types) if job_types else ("Remote" if is_remote else "Full-time")

                job_id = JobListing.generate_id(title, company, location)

                listing = JobListing(
                    id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    city=location,
                    country="Germany",
                    source_platform="Arbeitnow",
                    found_on=["Arbeitnow"],
                    job_url=job_url,
                    direct_apply_url=direct_apply_url or job_url,
                    application_platform=app_platform,
                    application_type=app_type,
                    how_to_apply=how_to_apply,
                    is_remote=is_remote,
                    job_type=job_type_str,
                    date_posted=date_str,
                    salary="Competitive (See listing)",
                    description_snippet=clean_text[:350] + "..." if len(clean_text) > 350 else clean_text,
                    tags=tags[:5],
                )
                results.append(listing)
                if len(results) >= filters.results_per_source:
                    break

            if progress_callback:
                progress_callback(f"Arbeitnow: {len(results)} matching jobs found.")

        except Exception as e:
            logger.error(f"Error querying Arbeitnow: {e}", exc_info=True)
            if progress_callback:
                progress_callback(f"Arbeitnow error: {str(e)}")

        return results
