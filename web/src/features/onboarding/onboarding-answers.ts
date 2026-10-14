import { normalizeTerms } from '../../lib/term-list';
import type { EditableConfig } from '../../types/config';

export type Seniority = 'entry' | 'mid' | 'senior' | 'lead';

export interface OnboardingAnswers {
  role: string;
  keywords: string[];
  remoteOnly: boolean;
  blockedRegions: string[];
  seniority: Seniority;
}

export const SENIORITY_OPTIONS: ReadonlyArray<{ value: Seniority; label: string; hint: string }> = [
  { value: 'entry', label: 'Entry level', hint: 'Just starting out, or up to about two years in.' },
  { value: 'mid', label: 'Mid level', hint: 'Solid experience, working on your own.' },
  { value: 'senior', label: 'Senior', hint: 'Deep experience, mentoring others.' },
  { value: 'lead', label: 'Lead or above', hint: 'Leading teams or setting direction.' },
];

const TITLE_PREFIX: Record<Seniority, string> = {
  entry: 'Junior ',
  mid: '',
  senior: 'Senior ',
  lead: 'Lead ',
};

const AVOID_BY_SENIORITY: Record<Seniority, string[]> = {
  entry: ['senior', 'lead', 'staff', 'principal', 'director', 'head of'],
  mid: ['intern', 'director', 'head of'],
  senior: ['intern', 'junior'],
  lead: ['intern', 'junior'],
};

export const EMPTY_ANSWERS: OnboardingAnswers = {
  role: '',
  keywords: [],
  remoteOnly: true,
  blockedRegions: [],
  seniority: 'mid',
};

function withSeniority(role: string, seniority: Seniority): string {
  const prefix = TITLE_PREFIX[seniority];
  const trimmed = role.trim();
  return !prefix || trimmed.toLowerCase().startsWith(prefix.trim().toLowerCase())
    ? trimmed
    : `${prefix}${trimmed}`;
}

/** Layer the four answers over the existing config so every other setting is kept. */
export function applyAnswers(base: EditableConfig, answers: OnboardingAnswers): EditableConfig {
  return {
    ...base,
    profile: {
      ...base.profile,
      role: withSeniority(answers.role, answers.seniority),
      includeKeywords: normalizeTerms(answers.keywords),
      excludeKeywords: AVOID_BY_SENIORITY[answers.seniority],
      remoteOnly: answers.remoteOnly,
      blockedRegions: normalizeTerms(answers.blockedRegions),
    },
  };
}
