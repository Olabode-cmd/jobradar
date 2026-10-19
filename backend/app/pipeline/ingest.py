"""Normalize, dedupe, judge and store one source's records.

Filter-then-store: a job that fails the profile rules is dropped before it reaches the
database. Drops are counted, with their reasons, in the run stats so a run can still
answer "what did RemoteOK drop today?". Dropped jobs are not remembered, so a profile
change takes effect on the next fetch.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from ..db.repositories import ingest as store
from ..domain.eligibility import evaluate
from ..domain.job import is_usable, normalize_job
from ..domain.scoring import score_job


@dataclass
class SeenIndex:
    """What is already known, so duplicates are caught across sources and across runs."""

    url_to_id: dict[str, int] = field(default_factory=dict)
    hash_to_id: dict[str, int] = field(default_factory=dict)
    urls: set[str] = field(default_factory=set)  # seen this run (also covers dry runs)
    hashes: set[str] = field(default_factory=set)

    @classmethod
    def from_db(cls, conn: sqlite3.Connection) -> "SeenIndex":
        return cls(url_to_id=store.known_urls(conn), hash_to_id=store.known_hashes(conn))

    def match(self, url: str, digest: str | None) -> tuple[bool, int | None]:
        """(is a duplicate, id of the stored job it duplicates if any)."""
        if url in self.urls or url in self.url_to_id:
            return True, self.url_to_id.get(url)
        if digest and (digest in self.hashes or digest in self.hash_to_id):
            return True, self.hash_to_id.get(digest)
        return False, None

    def remember(self, url: str, digest: str | None, job_id: int | None = None) -> None:
        self.urls.add(url)
        if digest:
            self.hashes.add(digest)
        if job_id is not None:
            self.url_to_id[url] = job_id
            if digest:
                self.hash_to_id[digest] = job_id


def process_batch(
    conn: sqlite3.Connection,
    records: list[dict[str, Any]],
    source: dict[str, Any],
    profile: dict[str, Any],
    index: SeenIndex,
    now: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Returns fetched/new/known/skipped/dropped counts for the batch, plus `drop_reasons`."""
    stats: dict[str, Any] = {"fetched": len(records), "new": 0, "known": 0, "skipped": 0, "dropped": 0}
    drop_reasons: Counter[str] = Counter()

    for raw in records:
        if not is_usable(raw):
            stats["skipped"] += 1
            continue
        job = normalize_job(raw, source, now)
        url, digest = job["canonical_url"], job["dedupe_hash"]

        duplicate, existing_id = index.match(url, digest)
        if duplicate:
            if existing_id:
                store.reopen_if_reposted(conn, existing_id, job["posted_at"], now)
                store.attach_source(conn, existing_id, source["id"], url, now)
            stats["known"] += 1
            continue

        job["eligibility"], reason = evaluate(job, profile)
        if job["eligibility"] != "eligible":
            stats["dropped"] += 1
            drop_reasons[reason or job["eligibility"]] += 1
            continue

        job["score"], job["score_reasons"] = score_job(job, profile)

        if dry_run:
            index.remember(url, digest)
        else:
            job_id = store.insert_job(conn, job, now)
            index.remember(url, digest, job_id)
            store.attach_source(conn, job_id, source["id"], url, now)
        stats["new"] += 1

    stats["drop_reasons"] = dict(drop_reasons.most_common())
    return stats
