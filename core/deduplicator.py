"""Job listing deduplication and multi-platform merging."""

import re
from typing import List, Dict
from core.models import JobListing

CLEAN_SUFFIXES = re.compile(
    r"\b(m/w/d|m/f/d|w/m/d|all genders|gn|d/m/w|m/w/x|w/m/div|gesucht)\b|[\[\(\]\)]",
    re.IGNORECASE
)

CLEAN_COMPANY = re.compile(
    r"\b(gmbh|ag|se|inc|ltd|co\.?\s*kg|holding|deutschland|germany|group|gruppe)\b|[,\.\-\(\)]",
    re.IGNORECASE
)

def normalize_title(title: str) -> str:
    cleaned = CLEAN_SUFFIXES.sub("", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned

def normalize_company(company: str) -> str:
    cleaned = CLEAN_COMPANY.sub("", company)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned

def normalize_city(city: str) -> str:
    if not city:
        return "germany"
    cleaned = city.lower().split(",")[0].strip()
    return cleaned

class Deduplicator:
    """Merges matching job listings from multiple sources into a single consolidated record."""

    @staticmethod
    def deduplicate(listings: List[JobListing]) -> List[JobListing]:
        """
        Deduplicates listings by normalized title + company + city.
        Combines `found_on` platforms and prioritizes Direct ATS application links.
        """
        merged_map: Dict[str, JobListing] = {}

        for job in listings:
            norm_t = normalize_title(job.title)
            norm_c = normalize_company(job.company)
            norm_l = normalize_city(job.city or job.location)

            key = f"{norm_t}|{norm_c}|{norm_l}"

            if key not in merged_map:
                merged_map[key] = job
                if job.source_platform and job.source_platform not in job.found_on:
                    job.found_on.append(job.source_platform)
            else:
                existing = merged_map[key]

                # Merge found_on platforms
                for platform in (job.found_on or [job.source_platform]):
                    if platform and platform not in existing.found_on:
                        existing.found_on.append(platform)

                # Prioritize Direct ATS over Job Board / Aggregator
                is_existing_ats = existing.application_type == "Direct ATS"
                is_new_ats = job.application_type == "Direct ATS"

                if not is_existing_ats and is_new_ats:
                    existing.direct_apply_url = job.direct_apply_url
                    existing.application_platform = job.application_platform
                    existing.application_type = job.application_type
                    existing.how_to_apply = job.how_to_apply

                # If existing is missing description snippet, take newer
                if (not existing.description_snippet or len(existing.description_snippet) < 50) and job.description_snippet:
                    existing.description_snippet = job.description_snippet

                # Combine tags
                for tag in job.tags:
                    if tag and tag not in existing.tags:
                        existing.tags.append(tag)

                # Keep remote flag if either has it
                if job.is_remote:
                    existing.is_remote = True

        return list(merged_map.values())
