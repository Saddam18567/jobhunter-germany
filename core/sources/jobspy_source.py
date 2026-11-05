"""JobSpy source adapter for LinkedIn, Indeed (Germany), Glassdoor, Google Jobs, etc."""

import logging
import math
import certifi
from typing import List, Callable, Optional
import pandas as pd
from jobspy import scrape_jobs
from core.models import SearchFilters, JobListing
from core.sources.base import BaseJobSource
from core.ats_detector import ATSDetector

logger = logging.getLogger(__name__)

class JobSpySource(BaseJobSource):
    """Adapter for JobSpy scraping aggregator specifically configured for Germany."""

    def __init__(self, platform_id: str, display_name: str):
        super().__init__(display_name)
        self.platform_id = platform_id  # "linkedin", "indeed", "glassdoor", "google", "zip_recruiter"

    def search(
        self,
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        results: List[JobListing] = []
        if progress_callback:
            progress_callback(f"Scraping {self.name} for '{filters.keyword}' in Germany...")

        # Location formatting tailored per platform
        loc = (filters.location or "").strip()
        is_all_germany = not loc or loc.lower() in ["deutschland", "deutschland (ganzes land)", "germany", "all", ""]
        
        if is_all_germany:
            target_location = "Germany"
        else:
            clean_city = loc.split(",")[0].strip()
            # Glassdoor and Indeed require pure city names (e.g. "Berlin", "München")
            if self.platform_id in ["glassdoor", "indeed"]:
                target_location = clean_city or "Germany"
            else:
                target_location = f"{clean_city}, Germany" if "germany" not in loc.lower() and "deutschland" not in loc.lower() else loc

        hours_old = (filters.date_posted_days * 24) if filters.date_posted_days else None
        ca_cert_path = certifi.where()

        try:
            df: Optional[pd.DataFrame] = None
            try:
                df = scrape_jobs(
                    site_name=[self.platform_id],
                    search_term=filters.keyword,
                    location=target_location,
                    distance=filters.distance or 50,
                    is_remote=filters.is_remote,
                    country_indeed="germany",
                    results_wanted=min(filters.results_per_source, 50),
                    hours_old=hours_old,
                    ca_cert=ca_cert_path,
                    verbose=0
                )
            except Exception as scrape_err:
                logger.warning(f"Initial scrape for {self.name} raised: {scrape_err}")

            # Fallback for platforms (like Indeed) where strict is_remote adds 'MUST_NOT HYBRID'
            if (df is None or df.empty) and filters.is_remote:
                if progress_callback:
                    progress_callback(f"{self.name}: Retrying with relaxed remote filters for Germany...")
                try:
                    df = scrape_jobs(
                        site_name=[self.platform_id],
                        search_term=filters.keyword,
                        location=target_location,
                        distance=filters.distance or 50,
                        is_remote=False,
                        country_indeed="germany",
                        results_wanted=min(filters.results_per_source * 2, 50),
                        hours_old=hours_old,
                        ca_cert=ca_cert_path,
                        verbose=0
                    )
                except Exception as fb_err:
                    logger.warning(f"Relaxed fallback scrape for {self.name} failed: {fb_err}")

            if df is None or df.empty:
                if progress_callback:
                    progress_callback(f"{self.name}: 0 results returned.")
                return results

            if progress_callback:
                progress_callback(f"{self.name}: Retrieved {len(df)} listings. Analyzing ATS links...")

            for _, row in df.iterrows():
                title = str(row.get("title") or "Position").strip()
                company = str(row.get("company") or "Unknown Company").strip()
                job_location = str(row.get("location") or target_location).strip()
                job_url = str(row.get("job_url") or "").strip()
                job_url_direct = str(row.get("job_url_direct") or "").strip()
                if job_url_direct == "nan" or not job_url_direct:
                    job_url_direct = None

                description = str(row.get("description") or "")
                if description == "nan":
                    description = ""

                # Date parsing
                raw_date = row.get("date_posted")
                date_str = str(raw_date)[:10] if pd.notna(raw_date) else ""

                # Remote status detection
                is_remote_flag = bool(row.get("is_remote")) if pd.notna(row.get("is_remote")) else False
                desc_lower = description.lower()
                title_lower = title.lower()
                loc_lower = job_location.lower()
                
                is_remote = (
                    is_remote_flag or
                    "remote" in loc_lower or
                    "remote" in title_lower or
                    "homeoffice" in desc_lower or
                    "home-office" in desc_lower or
                    "mobiles arbeiten" in desc_lower or
                    "telearbeit" in desc_lower or
                    ("remote" in desc_lower and "germany" in desc_lower)
                )

                # Filter if remote was explicitly requested
                if filters.is_remote and not is_remote:
                    continue

                # Salary formatting
                min_amt = row.get("min_amount")
                max_amt = row.get("max_amount")
                currency = row.get("currency") or "EUR"
                if pd.notna(min_amt) and pd.notna(max_amt):
                    salary_str = f"{int(min_amt):,} - {int(max_amt):,} {currency}"
                elif pd.notna(min_amt):
                    salary_str = f"From {int(min_amt):,} {currency}"
                else:
                    salary_str = "Not specified"

                # ATS Detection
                app_platform, app_type, how_to_apply, best_url = ATSDetector.resolve_application_details(
                    source_platform=self.name,
                    job_url=job_url,
                    direct_url=job_url_direct,
                    description=description
                )

                job_id = JobListing.generate_id(title, company, job_location)

                listing = JobListing(
                    id=job_id,
                    title=title,
                    company=company,
                    location=job_location,
                    city=job_location.split(",")[0].strip(),
                    country="Germany",
                    source_platform=self.name,
                    found_on=[self.name],
                    job_url=job_url or best_url,
                    direct_apply_url=best_url or job_url,
                    application_platform=app_platform,
                    application_type=app_type,
                    how_to_apply=how_to_apply,
                    is_remote=is_remote,
                    job_type=str(row.get("job_type") or "Full-time"),
                    date_posted=date_str,
                    salary=salary_str,
                    description_snippet=description[:350] + "..." if len(description) > 350 else description,
                    tags=[t for t in [str(row.get("job_level")), str(row.get("job_function"))] if t and t != "nan"][:5]
                )
                results.append(listing)

            if progress_callback:
                progress_callback(f"{self.name}: {len(results)} jobs successfully processed.")

        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}", exc_info=True)
            if progress_callback:
                progress_callback(f"{self.name} scan encountered an issue: {str(e)[:80]}")

        return results
