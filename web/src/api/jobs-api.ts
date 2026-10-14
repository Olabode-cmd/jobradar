import { parseJobDetail, parseJobsPage } from '../lib/parse-jobs';
import type { JobDetail, JobQuery, JobStatus, JobsPage } from '../types/job';
import { toApiError } from './api-error';
import { http } from './http-client';

export async function fetchJobs(query: JobQuery): Promise<JobsPage> {
  try {
    const response = await http.get<unknown>('/jobs', {
      params: {
        status: query.status,
        eligibility: query.includeRestricted ? 'eligible,unclear,restricted' : 'eligible,unclear',
        q: query.query || undefined,
        remote_only: query.remoteOnly || undefined,
        sort: query.sort,
        limit: query.limit,
        offset: query.offset,
      },
    });
    return parseJobsPage(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function fetchJob(id: number): Promise<JobDetail> {
  try {
    const response = await http.get<unknown>(`/jobs/${id}`);
    return parseJobDetail(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function updateJob(
  id: number,
  changes: { status?: JobStatus; notes?: string },
): Promise<JobDetail> {
  try {
    const response = await http.patch<unknown>(`/jobs/${id}`, changes);
    return parseJobDetail(response.parsedBody);
  } catch (error) {
    throw toApiError(error);
  }
}

export async function bulkUpdateJobs(ids: number[], status: JobStatus): Promise<void> {
  try {
    await http.post('/jobs/bulk', { ids, status });
  } catch (error) {
    throw toApiError(error);
  }
}

export async function ignoreCompany(id: number): Promise<void> {
  try {
    await http.post(`/jobs/${id}/ignore-company`);
  } catch (error) {
    throw toApiError(error);
  }
}
