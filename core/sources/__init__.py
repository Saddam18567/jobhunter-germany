"""Job sources package."""

from core.sources.base import BaseJobSource
from core.sources.arbeitsagentur import ArbeitsagenturSource
from core.sources.arbeitnow import ArbeitnowSource
from core.sources.jobspy_source import JobSpySource

__all__ = [
    "BaseJobSource",
    "ArbeitsagenturSource",
    "ArbeitnowSource",
    "JobSpySource",
]
