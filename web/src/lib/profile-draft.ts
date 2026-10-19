import type { EditableConfig } from '../types/config';
import { isCountryCode } from './countries';
import { normalizeTerms } from './term-list';

export const MAX_AGE_DAYS_LIMIT = 3650;
const MAX_TEXT_LENGTH = 120;
const MAX_CONTACT_LENGTH = 200;

/** Form state: numbers stay as text so half-typed input never gets rewritten. */
export interface ProfileDraft {
  role: string;
  includeKeywords: string[];
  excludeKeywords: string[];
  rejectedPhrases: string[];
  remoteOnly: boolean;
  openToRelocation: boolean;
  targetCountries: string[];
  blockedRegions: string[];
  timezonesOverlap: string;
  minSalary: string;
  maxAgeDays: string;
  userAgentContact: string;
}

export type DraftErrors = Partial<Record<keyof ProfileDraft, string>>;

export function toDraft({ profile, preferences }: EditableConfig): ProfileDraft {
  return {
    role: profile.role,
    includeKeywords: profile.includeKeywords,
    excludeKeywords: profile.excludeKeywords,
    rejectedPhrases: profile.rejectedPhrases,
    remoteOnly: profile.remoteOnly,
    openToRelocation: profile.openToRelocation,
    targetCountries: profile.targetCountries,
    blockedRegions: profile.blockedRegions,
    timezonesOverlap: profile.timezonesOverlap ?? '',
    minSalary: profile.minSalary === null ? '' : String(profile.minSalary),
    maxAgeDays: profile.maxAgeDays === null ? '' : String(profile.maxAgeDays),
    userAgentContact: preferences.userAgentContact,
  };
}

function parseOptionalNumber(text: string): number | null {
  const trimmed = text.trim();
  if (!trimmed) return null;
  const value = Number(trimmed);
  return Number.isFinite(value) ? value : null;
}

/** Best-effort conversion: unparseable numbers become null. Use validateDraft before saving. */
export function toEditable(draft: ProfileDraft): EditableConfig {
  const timezones = draft.timezonesOverlap.trim();
  return {
    profile: {
      role: draft.role.trim(),
      includeKeywords: normalizeTerms(draft.includeKeywords),
      excludeKeywords: normalizeTerms(draft.excludeKeywords),
      rejectedPhrases: normalizeTerms(draft.rejectedPhrases),
      remoteOnly: draft.remoteOnly,
      openToRelocation: draft.openToRelocation,
      targetCountries: normalizeTerms(draft.targetCountries).map((code) => code.toUpperCase()),
      blockedRegions: normalizeTerms(draft.blockedRegions),
      timezonesOverlap: timezones || null,
      minSalary: parseOptionalNumber(draft.minSalary),
      maxAgeDays: parseOptionalNumber(draft.maxAgeDays),
    },
    preferences: { userAgentContact: draft.userAgentContact.trim() },
  };
}

export function validateDraft(draft: ProfileDraft): DraftErrors {
  const errors: DraftErrors = {};

  if (!draft.role.trim()) errors.role = 'Enter the job title you are looking for.';
  else if (draft.role.trim().length > MAX_TEXT_LENGTH) {
    errors.role = `Keep this under ${MAX_TEXT_LENGTH} characters.`;
  }

  const maxAge = draft.maxAgeDays.trim();
  if (maxAge) {
    const days = Number(maxAge);
    if (!Number.isInteger(days) || days < 1 || days > MAX_AGE_DAYS_LIMIT) {
      errors.maxAgeDays = `Use a whole number of days from 1 to ${MAX_AGE_DAYS_LIMIT}, or leave it empty.`;
    }
  }

  const minSalary = draft.minSalary.trim();
  if (minSalary) {
    const amount = Number(minSalary);
    if (!Number.isFinite(amount) || amount < 0) {
      errors.minSalary = 'Use a number of 0 or more, or leave it empty.';
    }
  }

  const badCountry = draft.targetCountries.find((code) => !isCountryCode(code));
  if (badCountry !== undefined) {
    errors.targetCountries = `Use two-letter country codes such as DE or JP ("${badCountry}" isn't one).`;
  }

  if (draft.timezonesOverlap.trim().length > MAX_TEXT_LENGTH) {
    errors.timezonesOverlap = `Keep this under ${MAX_TEXT_LENGTH} characters.`;
  }
  if (draft.userAgentContact.trim().length > MAX_CONTACT_LENGTH) {
    errors.userAgentContact = `Keep this under ${MAX_CONTACT_LENGTH} characters.`;
  }

  return errors;
}

export function isSameConfig(a: EditableConfig, b: EditableConfig): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
