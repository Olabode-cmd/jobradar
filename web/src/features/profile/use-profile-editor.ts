import { useCallback, useEffect, useMemo, useState } from 'react';

import { toApiError } from '../../api/api-error';
import {
  isSameConfig,
  toDraft,
  toEditable,
  validateDraft,
  type DraftErrors,
  type ProfileDraft,
} from '../../lib/profile-draft';
import type { ConfigSnapshot, EditableConfig } from '../../types/config';

export type SetDraftField = <K extends keyof ProfileDraft>(key: K, value: ProfileDraft[K]) => void;

export function useProfileEditor(
  initial: ConfigSnapshot,
  save: (update: EditableConfig) => Promise<ConfigSnapshot>,
) {
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(() => toDraft(initial.editable));
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [justSaved, setJustSaved] = useState(false);

  const preview = useMemo(() => toEditable(draft), [draft]);
  const baselineDraft = useMemo(() => toDraft(saved.editable), [saved]);
  const baseline = useMemo(() => toEditable(baselineDraft), [baselineDraft]);
  const errors = useMemo(() => validateDraft(draft), [draft]);

  // Numbers are compared as text too, so half-typed invalid input still counts as an edit.
  const dirty =
    !isSameConfig(preview, baseline) ||
    draft.minSalary.trim() !== baselineDraft.minSalary ||
    draft.maxAgeDays.trim() !== baselineDraft.maxAgeDays;

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  const setField = useCallback<SetDraftField>((key, value) => {
    setDraft((current) => ({ ...current, [key]: value }));
    setJustSaved(false);
    setSaveError(null);
  }, []);

  const discard = useCallback(() => {
    setDraft(baselineDraft);
    setShowErrors(false);
    setSaveError(null);
    setJustSaved(false);
  }, [baselineDraft]);

  const submit = useCallback(async () => {
    if (saving) return;
    setShowErrors(true);
    if (Object.keys(errors).length > 0) return;

    setSaving(true);
    setSaveError(null);
    try {
      const next = await save(preview);
      setSaved(next);
      setDraft(toDraft(next.editable));
      setShowErrors(false);
      setJustSaved(true);
    } catch (error) {
      setSaveError(toApiError(error).message);
    } finally {
      setSaving(false);
    }
  }, [errors, preview, save, saving]);

  const visibleErrors: DraftErrors = showErrors ? errors : {};

  return {
    draft,
    preview,
    errors: visibleErrors,
    hasErrors: Object.keys(errors).length > 0,
    fileExists: saved.exists,
    dirty,
    saving,
    saveError,
    justSaved,
    setField,
    discard,
    submit,
  };
}

export type ProfileEditorState = ReturnType<typeof useProfileEditor>;
