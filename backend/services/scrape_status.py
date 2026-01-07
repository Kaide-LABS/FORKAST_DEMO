"""
Scrape status tracking service.

Provides in-memory tracking of background scrape jobs with status updates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
import asyncio


class ScrapeState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ScrapeJob:
    """Represents a scrape job status."""
    job_id: str
    source_type: str  # "operator" or "competitor"
    source_id: str
    platform: str
    url: str
    state: ScrapeState = ScrapeState.PENDING
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    items_scraped: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "platform": self.platform,
            "state": self.state.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "items_scraped": self.items_scraped,
            "error_message": self.error_message,
        }


class ScrapeStatusTracker:
    """
    In-memory tracker for scrape job statuses.

    Thread-safe using asyncio locks.
    """

    def __init__(self, max_jobs: int = 100):
        self._jobs: Dict[str, ScrapeJob] = {}
        self._lock = asyncio.Lock()
        self._max_jobs = max_jobs
        self._job_counter = 0

    async def create_job(
        self,
        source_type: str,
        source_id: str,
        platform: str,
        url: str,
    ) -> ScrapeJob:
        """Create a new scrape job and return it."""
        async with self._lock:
            self._job_counter += 1
            job_id = f"scrape_{self._job_counter}_{int(datetime.now().timestamp())}"

            job = ScrapeJob(
                job_id=job_id,
                source_type=source_type,
                source_id=source_id,
                platform=platform,
                url=url,
            )

            # Clean up old jobs if we have too many
            if len(self._jobs) >= self._max_jobs:
                oldest_key = min(self._jobs, key=lambda k: self._jobs[k].started_at)
                del self._jobs[oldest_key]

            self._jobs[job_id] = job
            return job

    async def update_state(
        self,
        job_id: str,
        state: ScrapeState,
        items_scraped: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the state of a scrape job."""
        async with self._lock:
            if job_id in self._jobs:
                job = self._jobs[job_id]
                job.state = state
                job.items_scraped = items_scraped
                job.error_message = error_message

                if state in (ScrapeState.SUCCESS, ScrapeState.FAILED, ScrapeState.TIMEOUT):
                    job.completed_at = datetime.now(timezone.utc)

    async def get_job(self, job_id: str) -> Optional[ScrapeJob]:
        """Get a scrape job by ID."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def get_latest_for_source(
        self,
        source_type: str,
        source_id: str,
    ) -> Optional[ScrapeJob]:
        """Get the latest scrape job for a source."""
        async with self._lock:
            matching = [
                j for j in self._jobs.values()
                if j.source_type == source_type and j.source_id == source_id
            ]
            if not matching:
                return None
            return max(matching, key=lambda j: j.started_at)

    async def get_active_jobs(self) -> list[ScrapeJob]:
        """Get all active (pending or running) jobs."""
        async with self._lock:
            return [
                j for j in self._jobs.values()
                if j.state in (ScrapeState.PENDING, ScrapeState.RUNNING)
            ]


# Global tracker instance
scrape_tracker = ScrapeStatusTracker()
