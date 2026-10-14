export const JOB_STATUSES = [
  'new',
  'saved',
  'applied',
  'interviewing',
  'rejected',
  'ignored',
] as const;
export type JobStatus = (typeof JOB_STATUSES)[number];

export type Eligibility = 'eligible' | 'unclear' | 'restricted';

export interface JobSummary {
  id: number;
  title: string;
  company: string;
  locationText: string;
  remote: boolean;
  postedAt: string | null;
  postedEstimated: boolean;
  score: number | null;
  eligibility: Eligibility | null;
  status: JobStatus;
  applyUrl: string | null;
  applyMethod: string | null;
  reposted: boolean;
  lowConfidence: boolean;
  sources: string[];
}

export interface SourceLink {
  sourceId: string;
  url: string;
}

export interface JobDetail extends JobSummary {
  description: string | null;
  salaryText: string | null;
  emails: string[];
  scoreReasons: string[];
  notes: string;
  sourceLinks: SourceLink[];
}

export type StatusCounts = Record<JobStatus, number>;

export interface JobsPage {
  items: JobSummary[];
  total: number;
  counts: StatusCounts;
}

export type JobSort = 'score' | 'recent';

export interface JobQuery {
  status: JobStatus | 'all';
  includeRestricted: boolean;
  query: string;
  remoteOnly: boolean;
  sort: JobSort;
  limit: number;
  offset: number;
}
