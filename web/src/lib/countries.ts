// Country codes the backend's countries.json catalog maps to Indeed, Wellfound and Relocate.me.
export const COUNTRY_SUGGESTIONS = ['DE', 'NL', 'CA', 'JP', 'UK', 'ES', 'PT', 'CY'] as const;

const COUNTRY_CODE = /^[A-Za-z]{2}$/;

export function isCountryCode(value: string): boolean {
  return COUNTRY_CODE.test(value.trim());
}
