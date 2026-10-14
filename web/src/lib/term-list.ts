export const MAX_TERMS = 200;
export const MAX_TERM_LENGTH = 120;

/** Trim, drop blanks and case-insensitive duplicates, keep first-seen order. */
export function normalizeTerms(terms: readonly string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const term of terms) {
    const text = term.trim();
    const key = text.toLowerCase();
    if (!text || text.length > MAX_TERM_LENGTH || seen.has(key)) continue;
    seen.add(key);
    result.push(text);
  }
  return result.slice(0, MAX_TERMS);
}

/** Add terms typed or pasted as comma- or newline-separated text. */
export function addTerms(current: readonly string[], rawInput: string): string[] {
  return normalizeTerms([...current, ...rawInput.split(/[,\n]/)]);
}

export function removeTerm(current: readonly string[], term: string): string[] {
  return current.filter((item) => item !== term);
}
