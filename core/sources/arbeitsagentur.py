"""Bundesagentur für Arbeit (Official German Federal Employment Agency) REST API Client."""

import logging
import requests
from typing import List, Callable, Optional
from config import BA_API_URL, BA_API_KEY, BA_JOB_DETAIL_URL
from core.models import SearchFilters, JobListing
from core.sources.base import BaseJobSource
from core.ats_detector import ATSDetector

logger = logging.getLogger(__name__)

class ArbeitsagenturSource(BaseJobSource):
    """Client for the official German federal Jobsuche REST API."""

    def __init__(self):
        super().__init__("Bundesagentur für Arbeit")
        self.headers = {
            "X-API-Key": BA_API_KEY,
            "User-Agent": "JobHunterGermany/1.0 (Mozilla/5.0; Desktop App)",
            "Accept": "application/json",
        }

    def search(
        self,
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        results: List[JobListing] = []
        if progress_callback:
            progress_callback(f"Connecting to official Bundesagentur für Arbeit API for '{filters.keyword}'...")

        params = {
            "was": filters.keyword,
            "size": min(filters.results_per_source, 100),
            "page": 1,
        }

        # Filter by location if not searching all Germany
        loc = (filters.location or "").strip()
        if loc and loc.lower() not in ["deutschland", "deutschland (ganzes land)", "germany", "all", ""]:
            params["wo"] = loc
            if filters.distance:
                params["umkreis"] = filters.distance

        # Filter by contract / working hours
        if filters.job_type == "fulltime":
            params["arbeitszeit"] = "vz"
        elif filters.job_type == "parttime":
            params["arbeitszeit"] = "tz"

        # Homeoffice / Remote
        if filters.is_remote:
            params["arbeitszeit"] = "ho"

        # Published since (days)
        if filters.date_posted_days:
            params["veroeffentlichtseit"] = filters.date_posted_days

        try:
            response = requests.get(
                BA_API_URL,
                headers=self.headers,
                params=params,
                timeout=12
            )

            if response.status_code != 200:
                logger.warning("Arbeitsagentur API returned status %s: %s", response.status_code, response.text[:200])
                if progress_callback:
                    progress_callback(f"Bundesagentur API response code: {response.status_code}")
                return results

            data = response.json()
            raw_jobs = data.get("ergebnisliste", [])

            if progress_callback:
                progress_callback(f"Bundesagentur API returned {len(raw_jobs)} listings. Parsing...")

            for item in raw_jobs:
                title = item.get("stellenangebotsTitel") or item.get("titel") or "Jobangebot"
                company = item.get("firma") or "Vertraulicher Arbeitgeber"
                refnr = item.get("referenznummer") or ""
                
                # Extract address / city
                locations = item.get("stellenlokationen", [])
                city_name = "Deutschland"
                full_loc = "Deutschland"
                if locations:
                    addr = locations[0].get("adresse", {})
                    city_name = addr.get("ort") or addr.get("region") or "Deutschland"
                    plz = addr.get("plz")
                    full_loc = f"{plz} {city_name}".strip() if plz else city_name

                # Remote / Homeoffice status
                is_remote = bool(item.get("homeofficemoeglich", False)) or filters.is_remote

                # Working time
                if item.get("arbeitszeitVollzeit"):
                    job_type = "Full-time (Vollzeit)"
                elif item.get("arbeitszeitTeilzeit"):
                    job_type = "Part-time (Teilzeit)"
                else:
                    job_type = "Vollzeit / Teilzeit"

                # Date posted
                pub_period = item.get("veroeffentlichungszeitraum", {})
                date_posted = pub_period.get("von") or item.get("datumErsteVeroeffentlichung", "")

                # URLs
                official_url = BA_JOB_DETAIL_URL.format(refnr=refnr) if refnr else "https://www.arbeitsagentur.de/jobsuche/"
                external_url = item.get("externeUrl")

                # Tags / Occupations
                tags = []
                hauptberuf = item.get("hauptberuf")
                if hauptberuf:
                    tags.append(hauptberuf)
                for b in item.get("alleBerufe", []):
                    if b not in tags:
                        tags.append(b)

                # Determine ATS and application details
                app_platform, app_type, how_to_apply, direct_apply_url = ATSDetector.resolve_application_details(
                    source_platform="Bundesagentur für Arbeit",
                    job_url=official_url,
                    direct_url=external_url,
                    description=title
                )

                if refnr and "Bundesagentur" in app_platform:
                    how_to_apply = f"Apply directly on Bundesagentur portal (Job-Ref: {refnr}) or contact {company}."

                job_id = JobListing.generate_id(title, company, city_name)

                listing = JobListing(
                    id=job_id,
                    title=title,
                    company=company,
                    location=full_loc,
                    city=city_name,
                    country="Germany",
                    source_platform="Bundesagentur für Arbeit",
                    found_on=["Bundesagentur für Arbeit"],
                    job_url=official_url,
                    direct_apply_url=direct_apply_url or official_url,
                    application_platform=app_platform,
                    application_type=app_type,
                    how_to_apply=how_to_apply,
                    is_remote=is_remote,
                    job_type=job_type,
                    date_posted=date_posted,
                    salary=item.get("verguetungsangabe", "Tarif / Vereinbarung"),
                    description_snippet=f"{hauptberuf or title} at {company} in {full_loc}.",
                    tags=tags[:5],
                )
                results.append(listing)

            if progress_callback:
                progress_callback(f"Bundesagentur für Arbeit: {len(results)} jobs collected successfully.")

        except Exception as e:
            logger.error(f"Error querying Bundesagentur für Arbeit: {e}", exc_info=True)
            if progress_callback:
                progress_callback(f"Bundesagentur für Arbeit error: {str(e)}")

        return results
