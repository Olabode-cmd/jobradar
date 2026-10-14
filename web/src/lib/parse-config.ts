import { ApiError } from '../api/api-error';
import type { ConfigSnapshot, EditableConfig, Profile } from '../types/config';
import { asNumberOrNull, asString, asStringList, isRecord } from './guards';

const DEFAULT_MAX_AGE_DAYS = 14;

// The backend accepts a string or a list here; the form edits it as one string.
function toTimezoneText(value: unknown): string | null {
  const text = Array.isArray(value) ? asStringList(value).join(', ') : value;
  return typeof text === 'string' && text.trim() ? text : null;
}

function parseProfile(raw: unknown): Profile {
  const source = isRecord(raw) ? raw : {};
  return {
    role: asString(source.role),
    includeKeywords: asStringList(source.includeKeywords),
    excludeKeywords: asStringList(source.excludeKeywords),
    rejectedPhrases: asStringList(source.rejectedPhrases),
    remoteOnly: typeof source.remoteOnly === 'boolean' ? source.remoteOnly : true,
    blockedRegions: asStringList(source.blockedRegions),
    timezonesOverlap: toTimezoneText(source.timezonesOverlap),
    minSalary: asNumberOrNull(source.minSalary),
    maxAgeDays:
      source.maxAgeDays === null
        ? null
        : (asNumberOrNull(source.maxAgeDays) ?? DEFAULT_MAX_AGE_DAYS),
  };
}

function parseEditable(config: Record<string, unknown>): EditableConfig {
  const preferences = isRecord(config.preferences) ? config.preferences : {};
  return {
    profile: parseProfile(config.profile),
    preferences: { userAgentContact: asString(preferences.userAgentContact) },
  };
}

export function parseConfigResponse(body: unknown): ConfigSnapshot {
  if (!isRecord(body) || typeof body.exists !== 'boolean' || !isRecord(body.config)) {
    throw new ApiError('unexpected', 'The API returned a config in an unexpected shape.');
  }
  return { exists: body.exists, editable: parseEditable(body.config) };
}
