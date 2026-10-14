import { Loading03Icon, Tick02Icon } from '@hugeicons/core-free-icons';
import { HugeiconsIcon } from '@hugeicons/react';

import { Button } from '../../components/ui/button';
import type { ProfileEditorState } from './use-profile-editor';

type SaveBarProps = Pick<
  ProfileEditorState,
  'dirty' | 'saving' | 'saveError' | 'justSaved' | 'hasErrors' | 'discard'
> & { showingErrors: boolean };

function statusMessage({
  dirty,
  saving,
  saveError,
  justSaved,
  showingErrors,
  hasErrors,
}: SaveBarProps) {
  if (saving) return { text: 'Saving…', tone: 'neutral' as const };
  if (saveError) return { text: saveError, tone: 'error' as const };
  if (showingErrors && hasErrors)
    return { text: 'Fix the highlighted fields to save.', tone: 'error' as const };
  if (justSaved) return { text: 'Saved to jobradar.config.json', tone: 'success' as const };
  if (dirty) return { text: 'You have unsaved changes.', tone: 'neutral' as const };
  return { text: 'Everything is saved.', tone: 'muted' as const };
}

const TONE_CLASSES = {
  neutral: 'text-white',
  muted: 'text-forest-300',
  success: 'text-lemon-400',
  error: 'text-danger',
} as const;

export function ProfileSaveBar(props: SaveBarProps) {
  const { dirty, saving, discard } = props;
  const { text, tone } = statusMessage(props);

  return (
    <div className="sticky bottom-4 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-forest-600 bg-forest-900 p-3 pl-5">
      <p
        role={tone === 'error' ? 'alert' : 'status'}
        className={`flex min-w-0 items-center gap-2 text-sm font-semibold ${TONE_CLASSES[tone]}`}
      >
        {tone === 'success' ? (
          <HugeiconsIcon icon={Tick02Icon} size={18} strokeWidth={2.5} />
        ) : null}
        {text}
      </p>
      <div className="flex gap-3">
        <Button variant="ghost" onClick={discard} disabled={!dirty || saving}>
          Discard changes
        </Button>
        <Button type="submit" disabled={!dirty || saving}>
          {saving ? (
            <HugeiconsIcon
              icon={Loading03Icon}
              size={18}
              strokeWidth={2.5}
              className="motion-safe:animate-spin"
            />
          ) : null}
          Save profile
        </Button>
      </div>
    </div>
  );
}
