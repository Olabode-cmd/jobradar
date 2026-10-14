import { HttpError, NetworkError, TimeoutError } from '@thraggs/godspeed';
export type ApiErrorKind = 'offline' | 'timeout' | 'conflict' | 'invalid' | 'server' | 'unexpected';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;

  constructor(kind: ApiErrorKind, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = 'ApiError';
    this.kind = kind;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** FastAPI returns `detail` as a string, or as a list of {loc, msg} for validation errors. */
function describeDetail(body: unknown): string | null {
  if (!isRecord(body)) return null;
  const { detail } = body;
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return null;

  const lines = detail.flatMap((item) => {
    if (!isRecord(item) || typeof item.msg !== 'string') return [];
    const path = Array.isArray(item.loc) ? item.loc.slice(2).join('.') : '';
    return [path ? `${path}: ${item.msg}` : item.msg];
  });
  return lines.length > 0 ? lines.join('; ') : null;
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;

  if (error instanceof TimeoutError) {
    return new ApiError('timeout', 'The API took too long to respond.', { cause: error });
  }
  if (error instanceof NetworkError) {
    return new ApiError(
      'offline',
      'Cannot reach the JobRadar API. Is the backend running on port 8000?',
      {
        cause: error,
      },
    );
  }
  if (error instanceof HttpError) {
    const detail = describeDetail(error.body);
    if (error.status === 409) {
      return new ApiError('conflict', detail ?? 'The config file cannot be read.', {
        cause: error,
      });
    }
    if (error.status === 422) {
      return new ApiError('invalid', detail ?? 'The API rejected these values.', { cause: error });
    }
    return new ApiError('server', detail ?? `The API returned status ${error.status}.`, {
      cause: error,
    });
  }
  return new ApiError('unexpected', 'Something went wrong talking to the API.', { cause: error });
}
