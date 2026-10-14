"""Ask the model whether a posting fits the candidate. Only the posting and search profile are sent, never a CV."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .client import LlmClient, LlmError

SYSTEM_PROMPT = (
    "You screen job postings for one candidate. Reply with ONLY a JSON object, no prose and no code fences."
)
MAX_DESCRIPTION_CHARS = 4000
MAX_REASON_CHARS = 200
_VERDICTS = ("yes", "no", "unclear")
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class Assessment:
    fit: int  # 0-10
    eligible: str  # "yes" | "no" | "unclear"
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"fit": self.fit, "eligible": self.eligible, "reason": self.reason}


def build_prompt(profile: dict[str, Any], job: dict[str, Any]) -> str:
    wanted = ", ".join(profile.get("includeKeywords") or []) or "none given"
    blocked = ", ".join(profile.get("blockedRegions") or []) or "none"
    description = (job.get("description") or "")[:MAX_DESCRIPTION_CHARS]
    return (
        "Candidate search profile:\n"
        f"- Target role: {profile.get('role') or 'not stated'}\n"
        f"- Wanted skills: {wanted}\n"
        f"- Must be remote: {'yes' if profile.get('remoteOnly') else 'no'}\n"
        f"- Cannot work in (no right to work there): {blocked}\n\n"
        "Job posting:\n"
        f"- Title: {job.get('title')}\n"
        f"- Company: {job.get('company')}\n"
        f"- Location: {job.get('location_text') or 'not stated'}\n"
        f"- Pay: {job.get('salary_text') or 'not stated'}\n"
        f"- Description: {description or 'not provided'}\n\n"
        'Answer with {"fit": <integer 0-10 for how well the job matches the role and skills>, '
        '"eligible": "yes" | "no" | "unclear" (can the candidate apply given the remote requirement and the '
        'regions they cannot work in?), "reason": "<one short sentence>"}.'
    )


def parse_assessment(text: str) -> Assessment:
    match = _JSON_OBJECT.search(text or "")
    try:
        data = json.loads(match.group(0)) if match else None
        fit = int(round(float(data["fit"])))
        eligible = str(data["eligible"]).strip().lower()
        reason = " ".join(str(data.get("reason", "")).split())[:MAX_REASON_CHARS]
    except (ValueError, KeyError, TypeError, AttributeError):
        raise LlmError("unexpected", "The model's answer wasn't the JSON we asked for.") from None
    if eligible not in _VERDICTS:
        raise LlmError("unexpected", "The model's answer had an unknown eligibility value.")
    return Assessment(fit=max(0, min(10, fit)), eligible=eligible, reason=reason)


def assess_job(client: LlmClient, profile: dict[str, Any], job: dict[str, Any]) -> Assessment:
    reply = client.complete(SYSTEM_PROMPT, build_prompt(profile, job), max_tokens=200)
    return parse_assessment(reply.text)
