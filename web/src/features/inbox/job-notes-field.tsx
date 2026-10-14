import { useId, useState } from 'react';

interface JobNotesFieldProps {
  initialValue: string;
  onSave: (notes: string) => void;
}

export function JobNotesField({ initialValue, onSave }: JobNotesFieldProps) {
  const id = useId();
  const [value, setValue] = useState(initialValue);
  const [savedValue, setSavedValue] = useState(initialValue);

  const saveIfChanged = () => {
    if (value === savedValue) return;
    setSavedValue(value);
    onSave(value);
  };

  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-bold">
        Notes
      </label>
      <textarea
        id={id}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onBlur={saveIfChanged}
        rows={3}
        maxLength={5000}
        placeholder="Recruiter name, follow-up date, anything worth remembering"
        className="w-full resize-y rounded-lg border border-border bg-input px-3.5 py-2.5 text-sm font-medium outline-none placeholder:text-muted/60 hover:border-border-dim focus:border-accent"
      />
    </div>
  );
}
