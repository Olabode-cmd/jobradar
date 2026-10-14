import { ApiError } from '../api/api-error';
import {
  JOB_STATUSES,
  type ContactEmail,
  type Eligibility,
  type JobDetail,
  type JobStatus,
  type JobSummary,
  type JobsPage,
  type StatusCounts,
} from '../types/job';
import { asNumberOrNull, asString, asStringList, asStringOrNull, isRecord } from './guards';

const ELIGIBILITIES: readonly Eligibility[] = ['eligible', 'unclear', 'restricted'];

function malformed(what: string): ApiError {
  return new ApiError('unexpected', `The API returned ${what} in an unexpected shape.`);
}

function asStatus(value: unknown): JobStatus {
  return JOB_STATUSES.find((status) => status === value) ?? 'new';
}

function asEligibility(value: unknown): Eligibility | null {
  return ELIGIBILITIES.find((item) => item === value) ?? null;
}

function parseSummary(raw: Record<string, unknown>): JobSummary | null {
  const id = asNumberOrNull(raw.id);
  if (id === null) return null;
  return {
    id,
    title: asString(raw.title, 'Untitled'),
    company: asString(raw.company, 'Unknown company'),
    locationText: asString(raw.location_text),
    remote: raw.remote === true,
    postedAt: asStringOrNull(raw.posted_at),
    postedEstimated: raw.posted_estimated === true,
    score: asNumberOrNull(raw.score),
    eligibility: asEligibility(raw.eligibility),
    status: asStatus(raw.status),
    applyUrl: asStringOrNull(raw.apply_url),
    applyMethod: asStringOrNull(raw.apply_method),
    reposted: raw.reposted === true,
    lowConfidence: raw.low_confidence === true,
    sources: asStringList(raw.sources),
  };
}

function parseEmails(raw: unknown): ContactEmail[] {
  if (!Array.isArray(raw)) return [];
  return raw.flatMap((item) =>
    isRecord(item) && typeof item.address === 'string'
      ? [{ address: item.address, generic: item.generic === true }]
      : [],
  );
}

function parseCounts(raw: unknown): StatusCounts {
  const source = isRecord(raw) ? raw : {};
  const counts = {} as StatusCounts;
  for (const status of JOB_STATUSES) counts[status] = asNumberOrNull(source[status]) ?? 0;
  return counts;
}

export function parseJobsPage(body: unknown): JobsPage {
  if (!isRecord(body) || !Array.isArray(body.items)) throw malformed('a job list');
  const items = body.items.flatMap((item) => {
    const summary = isRecord(item) ? parseSummary(item) : null;
    return summary ? [summary] : [];
  });
  return {
    items,
    total: asNumberOrNull(body.total) ?? items.length,
    counts: parseCounts(body.counts),
  };
}

export function parseJobDetail(body: unknown): JobDetail {
  const summary = isRecord(body) ? parseSummary(body) : null;
  if (!isRecord(body) || !summary) throw malformed('a job');

  const sourceLinks = Array.isArray(body.source_links)
    ? body.source_links.flatMap((link) =>
        isRecord(link) && typeof link.url === 'string'
          ? [{ sourceId: asString(link.source_id), url: link.url }]
          : [],
      )
    : [];

  return {
    ...summary,
    description: asStringOrNull(body.description),
    salaryText: asStringOrNull(body.salary_text),
    emails: parseEmails(body.emails),
    scoreReasons: asStringList(body.score_reasons),
    notes: asString(body.notes),
    sourceLinks,
  };
}
