import { useId } from 'react';

import { Switch } from './switch';

interface ToggleFieldProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function ToggleField({ label, description, checked, onChange }: ToggleFieldProps) {
  const id = useId();
  const labelId = `${id}-label`;
  const descriptionId = `${id}-description`;

  return (
    <div className="flex items-start justify-between gap-6">
      <div>
        <span id={labelId} className="block text-sm font-bold">
          {label}
        </span>
        <p id={descriptionId} className="mt-1 text-sm text-forest-300">
          {description}
        </p>
      </div>
      <Switch
        checked={checked}
        onChange={onChange}
        aria-labelledby={labelId}
        aria-describedby={descriptionId}
      />
    </div>
  );
}
