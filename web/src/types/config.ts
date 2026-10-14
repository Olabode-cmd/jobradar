export interface Profile {
  role: string;
  includeKeywords: string[];
  excludeKeywords: string[];
  rejectedPhrases: string[];
  remoteOnly: boolean;
  blockedRegions: string[];
  timezonesOverlap: string | null;
  minSalary: number | null;
  maxAgeDays: number | null;
}

export interface Preferences {
  userAgentContact: string;
}

/** The slice of jobradar.config.json that this dashboard edits. */
export interface EditableConfig {
  profile: Profile;
  preferences: Preferences;
}

export interface ConfigSnapshot {
  exists: boolean;
  editable: EditableConfig;
}
