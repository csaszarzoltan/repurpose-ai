"""CRUD repository — analytics data store with in-memory storage.

Source of truth: analysis/analysis-brief.md §4 P0.1.
"""

from __future__ import annotations

from uuid import uuid4


class MetricsRepository:
    """Time-series metrics storage and retrieval (in-memory)."""

    def __init__(self) -> None:
        self._metrics: list[dict] = []

    async def store_metrics(
        self,
        platform: str,
        post_id: str,
        metrics: dict,
    ) -> str:
        """Store metrics and return a post ID."""
        entry = {"platform": platform, "post_id": post_id, **metrics}
        self._metrics.append(entry)
        return post_id

    async def query_metrics(
        self,
        platform: str,
        from_date: object,
        to_date: object,
        granularity: str = "daily",
    ) -> list[dict]:
        """Query stored metrics (returns all matching platform entries)."""
        return [m for m in self._metrics if m.get("platform") == platform]


class ValidationRepository:
    """Validation report storage and retrieval (in-memory)."""

    def __init__(self) -> None:
        self._validations: dict[str, dict] = {}

    async def store_validation(
        self,
        job_id: str,
        draft: str,
        published: str,
        scores: dict,
    ) -> str:
        """Store a validation result and return the job ID."""
        self._validations[job_id] = {
            "job_id": job_id,
            "draft": draft,
            "published": published,
            **scores,
        }
        return job_id

    async def query_validation(self, job_id: str) -> dict:
        """Retrieve a validation report by job ID."""
        return self._validations.get(job_id, {})


class ScoreRepository:
    """Optimization score storage and retrieval (in-memory)."""

    def __init__(self) -> None:
        self._scores: dict[str, dict] = {}

    async def store_score(
        self,
        post_id: str,
        platform: str,
        overall_score: float,
        signals: dict[str, float],
    ) -> str:
        """Store a score and return a unique ID."""
        score_id = str(uuid4())
        self._scores[score_id] = {
            "id": score_id,
            "post_id": post_id,
            "platform": platform,
            "overall_score": overall_score,
            "signals": signals,
        }
        return score_id

    async def query_score(self, post_id: str, platform: str) -> dict:
        """Retrieve a score by post ID and platform."""
        for entry in self._scores.values():
            if entry.get("post_id") == post_id and entry.get("platform") == platform:
                return entry
        return {}
