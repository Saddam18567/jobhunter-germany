"""Concurrent Job Search Orchestrator across German APIs and scrapers."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
from core.models import SearchFilters, JobListing
from core.sources.base import BaseJobSource
from core.sources.arbeitsagentur import ArbeitsagenturSource
from core.sources.arbeitnow import ArbeitnowSource
from core.sources.jobspy_source import JobSpySource
from core.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

class JobAggregator:
    """Manages concurrent execution of multiple job sources."""

    def __init__(self):
        self.sources_map: Dict[str, BaseJobSource] = {
            "arbeitsagentur": ArbeitsagenturSource(),
            "arbeitnow": ArbeitnowSource(),
            "linkedin": JobSpySource("linkedin", "LinkedIn"),
            "indeed": JobSpySource("indeed", "Indeed Germany"),
            "glassdoor": JobSpySource("glassdoor", "Glassdoor"),
            "google": JobSpySource("google", "Google Jobs"),
            "zip_recruiter": JobSpySource("zip_recruiter", "ZipRecruiter"),
        }

    def get_source_instances(self, requested_sources: List[str]) -> List[BaseJobSource]:
        """Resolve requested source keys to source instances."""
        resolved = []
        for src_key in requested_sources:
            clean_key = src_key.lower().strip()
            if clean_key in self.sources_map:
                resolved.append(self.sources_map[clean_key])
            else:
                logger.warning(f"Unknown source requested: {src_key}")
        return resolved or list(self.sources_map.values())

    def search(
        self,
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        """
        Executes parallel search across selected sources, deduplicates,
        and returns consolidated job listings.
        """
        active_sources = self.get_source_instances(filters.sources)
        all_raw_listings: List[JobListing] = []

        if progress_callback:
            source_names = ", ".join([s.name for s in active_sources])
            progress_callback(f"Starting parallel job search across: {source_names}")

        # Execute searches in parallel with ThreadPoolExecutor
        max_workers = min(len(active_sources), 6)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_source = {
                executor.submit(source.search, filters, progress_callback): source
                for source in active_sources
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    source_results = future.result()
                    all_raw_listings.extend(source_results)
                    if progress_callback:
                        progress_callback(f"Finished fetching from {source.name}: {len(source_results)} items.")
                except Exception as e:
                    logger.error(f"Source {source.name} failed with error: {e}", exc_info=True)
                    if progress_callback:
                        progress_callback(f"{source.name} encountered an issue: {str(e)[:80]}")

        if progress_callback:
            progress_callback(f"Total raw listings gathered: {len(all_raw_listings)}. Deduplicating & ranking...")

        # Deduplicate and merge listings across platforms
        deduped_listings = Deduplicator.deduplicate(all_raw_listings)

        # Sort: Direct ATS first, then by date posted
        def sort_key(job: JobListing):
            is_ats = 1 if job.application_type == "Direct ATS" else 0
            date_val = job.date_posted or "1970-01-01"
            return (is_ats, date_val)

        deduped_listings.sort(key=sort_key, reverse=True)

        if progress_callback:
            ats_count = sum(1 for j in deduped_listings if j.application_type == "Direct ATS")
            progress_callback(
                f"Completed: {len(deduped_listings)} unique jobs found ({ats_count} with direct ATS links like Workday/Personio)."
            )

        return deduped_listings

    @staticmethod
    def calculate_stats(listings: List[JobListing]) -> Dict[str, Any]:
        """Generate analytics and statistics for the results dashboard."""
        total = len(listings)
        ats_count = sum(1 for j in listings if j.application_type == "Direct ATS")
        remote_count = sum(1 for j in listings if j.is_remote)

        platform_counts: Dict[str, int] = {}
        ats_breakdown: Dict[str, int] = {}

        for j in listings:
            # Platforms
            for p in (j.found_on or [j.source_platform]):
                platform_counts[p] = platform_counts.get(p, 0) + 1
            
            # ATS breakdown
            if j.application_platform and j.application_platform not in ["Unknown", "Job Board"]:
                ats_breakdown[j.application_platform] = ats_breakdown.get(j.application_platform, 0) + 1

        return {
            "total_jobs": total,
            "direct_ats_jobs": ats_count,
            "remote_jobs": remote_count,
            "platform_distribution": platform_counts,
            "ats_distribution": ats_breakdown,
        }
