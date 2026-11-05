"""Base class for job scrapers and API clients."""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional
from core.models import SearchFilters, JobListing

class BaseJobSource(ABC):
    """Abstract base class for all job sources."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(
        self,
        filters: SearchFilters,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[JobListing]:
        """Execute search and return standardized job listings."""
        pass
