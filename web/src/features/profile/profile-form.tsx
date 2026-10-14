import { SectionPanel } from '../../components/ui/section-panel';
import { TagInput } from '../../components/ui/tag-input';
import { TextField } from '../../components/ui/text-field';
import { ToggleField } from '../../components/ui/toggle-field';
import type { DraftErrors, ProfileDraft } from '../../lib/profile-draft';
import { REGION_SUGGESTIONS } from '../../lib/regions';
import type { SetDraftField } from './use-profile-editor';

interface ProfileFormProps {
  draft: ProfileDraft;
  errors: DraftErrors;
  setField: SetDraftField;
}

export function ProfileForm({ draft, errors, setField }: ProfileFormProps) {
  return (
    <div className="space-y-6">
      <SectionPanel
        title="What you're looking for"
        description="Your target job and the words that describe it."
      >
        <TextField
          label="Job title"
          value={draft.role}
          onChange={(value) => setField('role', value)}
          placeholder="Frontend engineer"
          hint="The role you want, in plain words."
          error={errors.role}
          autoComplete="off"
        />
        <TagInput
          label="Keywords to include"
          value={draft.includeKeywords}
          onChange={(value) => setField('includeKeywords', value)}
          placeholder="react, typescript"
          hint="Press Enter or comma to add. Jobs that mention these rank higher."
        />
        <TagInput
          label="Keywords to avoid"
          value={draft.excludeKeywords}
          onChange={(value) => setField('excludeKeywords', value)}
          placeholder="senior, lead"
          hint="Jobs with these words in the title are marked restricted."
        />
      </SectionPanel>

      <SectionPanel title="Where you can work" description="Rules that mark a job as restricted.">
        <ToggleField
          label="Remote only"
          description="Hide jobs that aren't remote."
          checked={draft.remoteOnly}
          onChange={(value) => setField('remoteOnly', value)}
        />
        <TagInput
          label="Regions you can't work in"
          value={draft.blockedRegions}
          onChange={(value) => setField('blockedRegions', value)}
          placeholder="US"
          hint="Jobs that require living or working authorization in these regions are marked restricted."
          suggestions={REGION_SUGGESTIONS}
        />
        <TagInput
          label="Phrases to reject"
          value={draft.rejectedPhrases}
          onChange={(value) => setField('rejectedPhrases', value)}
          placeholder="must reside in"
          hint="Any posting containing one of these phrases is marked restricted."
        />
        <TextField
          label="Timezone overlap"
          value={draft.timezonesOverlap}
          onChange={(value) => setField('timezonesOverlap', value)}
          placeholder="UTC-1 to UTC+3"
          hint="Optional. The hours you can overlap with a team."
          error={errors.timezonesOverlap}
          autoComplete="off"
        />
      </SectionPanel>

      <SectionPanel title="Freshness and pay">
        <div className="grid gap-6 sm:grid-cols-2">
          <TextField
            label="Maximum posting age"
            value={draft.maxAgeDays}
            onChange={(value) => setField('maxAgeDays', value)}
            suffix="days"
            inputMode="numeric"
            placeholder="14"
            hint="Older postings are marked restricted. Leave empty for no limit."
            error={errors.maxAgeDays}
            autoComplete="off"
          />
          <TextField
            label="Minimum salary"
            value={draft.minSalary}
            onChange={(value) => setField('minSalary', value)}
            inputMode="decimal"
            placeholder="60000"
            hint="Optional. Yearly. Jobs that list a lower maximum are marked restricted."
            error={errors.minSalary}
            autoComplete="off"
          />
        </div>
      </SectionPanel>

      <SectionPanel title="Contact for job sites">
        <TextField
          label="Email or website"
          value={draft.userAgentContact}
          onChange={(value) => setField('userAgentContact', value)}
          placeholder="you@example.com"
          hint="Optional. Sent with each fetch so a site can reach you if it causes trouble."
          error={errors.userAgentContact}
          autoComplete="off"
        />
      </SectionPanel>
    </div>
  );
}
