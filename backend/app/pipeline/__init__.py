"""Fetch → normalize → dedupe → judge → store, with a single-flight run lock."""

from .doctor import run_doctor
from .progress import PROGRESS, RunProgress
from .runner import begin_run, execute_run, run_fetch, select_sources

__all__ = ["PROGRESS", "RunProgress", "begin_run", "execute_run", "run_doctor", "run_fetch", "select_sources"]
