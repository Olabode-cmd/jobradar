import { useNavigate } from 'react-router-dom';

import { Banner } from '../../components/ui/banner';
import { Button } from '../../components/ui/button';
import { QUESTIONS } from './questions';
import { STEP_COUNT, useOnboarding } from './use-onboarding';

export function OnboardingPage() {
  const navigate = useNavigate();
  const flow = useOnboarding();

  if (flow.loadError) {
    return (
      <Banner tone="error" title="Couldn't start setup">
        {flow.loadError}
      </Banner>
    );
  }
  if (!flow.ready) return <p className="text-muted">Loading…</p>;

  if (flow.saved) {
    const fetchNow = async () => {
      if (await flow.fetchFirstJobs()) navigate('/runs');
    };
    return (
      <div className="max-w-xl">
        <h1 className="text-4xl font-extrabold tracking-tight">Your radar is set</h1>
        <p className="mt-3 text-muted">
          Your search is saved. Fetch jobs now to see the first matches, or look around first. You
          can change anything later on the Profile page.
        </p>
        {flow.error ? (
          <div className="mt-6">
            <Banner tone="error" title="Couldn't start the fetch">
              {flow.error}
            </Banner>
          </div>
        ) : null}
        <div className="mt-8 flex flex-wrap gap-3">
          <Button onClick={() => void fetchNow()} disabled={flow.busy}>
            Fetch jobs now
          </Button>
          <Button variant="ghost" onClick={() => navigate('/inbox')}>
            Skip for now
          </Button>
        </div>
      </div>
    );
  }

  const current = QUESTIONS[flow.step]!;
  const isLast = flow.step === STEP_COUNT - 1;

  return (
    <div className="max-w-2xl">
      <p className="text-sm font-bold text-muted">
        Question {flow.step + 1} of {STEP_COUNT}
      </p>
      <h1 className="mt-2 mb-8 text-4xl font-extrabold tracking-tight">{current.title}</h1>

      <current.Component answers={flow.answers} update={flow.update} />

      {flow.error ? (
        <div className="mt-6">
          <Banner tone="error" title="Couldn't save your answers">
            {flow.error}
          </Banner>
        </div>
      ) : null}

      <div className="mt-10 flex gap-3">
        {flow.step > 0 ? (
          <Button variant="ghost" onClick={flow.back} disabled={flow.busy}>
            Back
          </Button>
        ) : null}
        {isLast ? (
          <Button onClick={() => void flow.finish()} disabled={flow.busy}>
            {flow.busy ? 'Saving…' : 'Save and finish'}
          </Button>
        ) : (
          <Button onClick={flow.next} disabled={!flow.canAdvance}>
            Next
          </Button>
        )}
      </div>
    </div>
  );
}
