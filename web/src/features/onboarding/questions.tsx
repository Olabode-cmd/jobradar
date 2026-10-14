import { ChoiceGroup } from '../../components/ui/choice-group';
import { TagInput } from '../../components/ui/tag-input';
import { TextField } from '../../components/ui/text-field';
import { cn } from '../../lib/class-names';
import { REGION_SUGGESTIONS } from '../../lib/regions';
import { SENIORITY_OPTIONS, type OnboardingAnswers, type Seniority } from './onboarding-answers';
import { ROLE_TEMPLATES } from './role-templates';

interface QuestionProps {
  answers: OnboardingAnswers;
  update: <K extends keyof OnboardingAnswers>(key: K, value: OnboardingAnswers[K]) => void;
}

export function RoleQuestion({ answers, update }: QuestionProps) {
  const applyTemplate = (id: string) => {
    const template = ROLE_TEMPLATES.find((item) => item.id === id);
    if (!template) return;
    update('role', template.role);
    update('keywords', [...template.keywords]);
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="mb-2 text-sm font-bold">Start from a template</p>
        <div className="flex flex-wrap gap-2">
          {ROLE_TEMPLATES.map((template) => {
            const active = answers.role === template.role;
            return (
              <button
                key={template.id}
                type="button"
                aria-pressed={active}
                onClick={() => applyTemplate(template.id)}
                className={cn(
                  'h-10 rounded-lg border px-4 text-sm font-bold transition-colors',
                  active
                    ? 'border-lemon-400 bg-lemon-400 text-ink'
                    : 'border-forest-600 hover:border-forest-300',
                )}
              >
                {template.label}
              </button>
            );
          })}
        </div>
      </div>
      <TextField
        label="Job title"
        value={answers.role}
        onChange={(value) => update('role', value)}
        placeholder="Frontend engineer"
        hint="Or type your own."
        autoComplete="off"
      />
      <TagInput
        label="Skills and keywords"
        value={answers.keywords}
        onChange={(value) => update('keywords', value)}
        placeholder="react, typescript"
        hint="Jobs that mention these rank higher. Press Enter or comma to add."
      />
    </div>
  );
}

export function RemoteQuestion({ answers, update }: QuestionProps) {
  return (
    <ChoiceGroup
      legend="Remote preference"
      value={answers.remoteOnly ? 'remote' : 'any'}
      onChange={(value) => update('remoteOnly', value === 'remote')}
      options={[
        { value: 'remote', label: 'Remote only', hint: 'Hide anything that is not remote.' },
        {
          value: 'any',
          label: 'Open to on-site or hybrid too',
          hint: 'Remote jobs still rank higher.',
        },
      ]}
    />
  );
}

export function RegionsQuestion({ answers, update }: QuestionProps) {
  return (
    <TagInput
      label="Regions you can't work in"
      value={answers.blockedRegions}
      onChange={(value) => update('blockedRegions', value)}
      placeholder="US"
      hint="Jobs that require living or working authorization there are marked restricted. Leave empty if none."
      suggestions={REGION_SUGGESTIONS}
    />
  );
}

export function SeniorityQuestion({ answers, update }: QuestionProps) {
  return (
    <ChoiceGroup<Seniority>
      legend="Seniority"
      value={answers.seniority}
      onChange={(value) => update('seniority', value)}
      options={SENIORITY_OPTIONS}
    />
  );
}

export const QUESTIONS = [
  { title: 'What job are you looking for?', Component: RoleQuestion },
  { title: 'Do you want remote work only?', Component: RemoteQuestion },
  { title: 'Where can you not work?', Component: RegionsQuestion },
  { title: 'How senior are you?', Component: SeniorityQuestion },
] as const;
