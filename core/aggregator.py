"""Concurrent Job Search Orchestrator across German APIs, scrapers, and multiple keywords."""

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
    """Manages concurrent execution of multiple job sources and multiple keywords."""

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

    def _search_single_keyword(
        self,
        active_sources: List[BaseJobSource],
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        """Execute parallel search across sources for a single keyword."""
        listings: List[JobListing] = []
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
                    listings.extend(source_results)
                except Exception as e:
                    logger.error(f"Source {source.name} failed with error: {e}", exc_info=True)
                    if progress_callback:
                        progress_callback(f"{source.name} issue: {str(e)[:80]}")

        return listings

    def search(
        self,
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        """
        Executes search across selected sources and multiple keywords,
        deduplicates, and returns consolidated job listings.
        """
        active_sources = self.get_source_instances(filters.sources)
        keywords = filters.keywords_list
        if not keywords:
            keywords = [filters.keyword or "Jobs"]

        all_raw_listings: List[JobListing] = []
        total_kw = len(keywords)

        if progress_callback:
            source_names = ", ".join([s.name for s in active_sources])
            if total_kw > 1:
                kw_preview = ", ".join(keywords[:3]) + ("..." if total_kw > 3 else "")
                progress_callback(f"Starting multi-keyword search ({total_kw} terms: {kw_preview}) across {source_names}")
            else:
                progress_callback(f"Starting job search for '{keywords[0]}' across {source_names}")

        for idx, kw in enumerate(keywords, start=1):
            if progress_callback and total_kw > 1:
                progress_callback(f"[{idx}/{total_kw}] Searching for keyword '{kw}'...")

            # Create specific filter for this keyword
            single_filters = SearchFilters(
                keyword=kw,
                location=filters.location,
                distance=filters.distance,
                is_remote=filters.is_remote,
                job_type=filters.job_type,
                results_per_source=filters.results_per_source,
                sources=filters.sources,
                date_posted_days=filters.date_posted_days,
                save_directory=filters.save_directory
            )

            kw_results = self._search_single_keyword(active_sources, single_filters, progress_callback)
            
            for item in kw_results:
                if kw not in item.matched_keywords:
                    item.matched_keywords.append(kw)

            all_raw_listings.extend(kw_results)

        if progress_callback:
            progress_callback(f"Gathered {len(all_raw_listings)} listings across {total_kw} keyword(s). Deduplicating...")

        # Deduplicate across both platforms and keywords
        deduped_listings = Deduplicator.deduplicate(all_raw_listings)

        # Sort: Direct ATS first, then date posted
        def sort_key(job: JobListing):
            is_ats = 1 if job.application_type == "Direct ATS" else 0
            date_val = job.date_posted or "1970-01-01"
            return (is_ats, date_val)

        deduped_listings.sort(key=sort_key, reverse=True)

        if progress_callback:
            ats_count = sum(1 for j in deduped_listings if j.application_type == "Direct ATS")
            progress_callback(
                f"Complete: {len(deduped_listings)} unique jobs found ({ats_count} direct ATS links like Workday/Personio)."
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
        keyword_counts: Dict[str, int] = {}

        for j in listings:
            # Platforms
            for p in (j.found_on or [j.source_platform]):
                platform_counts[p] = platform_counts.get(p, 0) + 1
            
            # ATS breakdown
            if j.application_platform and j.application_platform not in ["Unknown", "Job Board"]:
                ats_breakdown[j.application_platform] = ats_breakdown.get(j.application_platform, 0) + 1

            # Keywords matched
            for kw in j.matched_keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        return {
            "total_jobs": total,
            "direct_ats_jobs": ats_count,
            "remote_jobs": remote_count,
            "platform_distribution": platform_counts,
            "ats_distribution": ats_breakdown,
            "keyword_distribution": keyword_counts,
        }
