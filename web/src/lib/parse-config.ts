import { ApiError } from '../api/api-error';
import type { ConfigSnapshot, EditableConfig, Profile } from '../types/config';

const DEFAULT_MAX_AGE_DAYS = 14;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function toStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string');
}

function toNumberOrNull(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

// The backend accepts a string or a list here; the form edits it as one string.
function toTimezoneText(value: unknown): string | null {
  const text = Array.isArray(value) ? toStringList(value).join(', ') : value;
  return typeof text === 'string' && text.trim() ? text : null;
}

function parseProfile(raw: unknown): Profile {
  const source = isRecord(raw) ? raw : {};
  return {
    role: typeof source.role === 'string' ? source.role : '',
    includeKeywords: toStringList(source.includeKeywords),
    excludeKeywords: toStringList(source.excludeKeywords),
    rejectedPhrases: toStringList(source.rejectedPhrases),
    remoteOnly: typeof source.remoteOnly === 'boolean' ? source.remoteOnly : true,
    blockedRegions: toStringList(source.blockedRegions),
    timezonesOverlap: toTimezoneText(source.timezonesOverlap),
    minSalary: toNumberOrNull(source.minSalary),
    maxAgeDays:
      source.maxAgeDays === null ? null : (toNumberOrNull(source.maxAgeDays) ?? DEFAULT_MAX_AGE_DAYS),
  };
}

function parseEditable(config: Record<string, unknown>): EditableConfig {
  const preferences = isRecord(config.preferences) ? config.preferences : {};
  return {
    profile: parseProfile(config.profile),
    preferences: {
      userAgentContact:
        typeof preferences.userAgentContact === 'string' ? preferences.userAgentContact : '',
    },
  };
}

export function parseConfigResponse(body: unknown): ConfigSnapshot {
  if (!isRecord(body) || typeof body.exists !== 'boolean' || !isRecord(body.config)) {
    throw new ApiError('unexpected', 'The API returned a config in an unexpected shape.');
  }
  return { exists: body.exists, editable: parseEditable(body.config) };
}
