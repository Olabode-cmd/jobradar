import type { FormEvent } from 'react';

import { Banner } from '../../components/ui/banner';
import type { ConfigSnapshot, EditableConfig } from '../../types/config';
import { ConfigFileSheet } from './config-file-sheet';
import { ProfileForm } from './profile-form';
import { ProfileSaveBar } from './profile-save-bar';
import { useProfileEditor } from './use-profile-editor';

interface ProfileEditorProps {
  snapshot: ConfigSnapshot;
  save: (update: EditableConfig) => Promise<ConfigSnapshot>;
}

export function ProfileEditor({ snapshot, save }: ProfileEditorProps) {
  const editor = useProfileEditor(snapshot, save);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void editor.submit();
  };

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_26rem]">
      <form onSubmit={handleSubmit} noValidate className="space-y-6">
        {!editor.fileExists ? (
          <Banner tone="info" title="No config file yet">
            Saving creates <strong>jobradar.config.json</strong> in the project folder.
          </Banner>
        ) : null}
        <ProfileForm draft={editor.draft} errors={editor.errors} setField={editor.setField} />
        <ProfileSaveBar
          dirty={editor.dirty}
          saving={editor.saving}
          saveError={editor.saveError}
          justSaved={editor.justSaved}
          hasErrors={editor.hasErrors}
          showingErrors={Object.keys(editor.errors).length > 0}
          discard={editor.discard}
        />
      </form>

      <ConfigFileSheet
        config={editor.preview}
        dirty={editor.dirty}
        fileExists={editor.fileExists}
      />
    </div>
  );
}
