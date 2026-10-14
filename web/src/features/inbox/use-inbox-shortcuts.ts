import { useEffect, useRef } from 'react';

import type { JobStatus } from '../../types/job';

interface ShortcutHandlers {
  onMove: (delta: 1 | -1) => void;
  onStatus: (status: JobStatus) => void;
  onOpenApply: () => void;
}

const STATUS_KEYS: Record<string, JobStatus> = {
  s: 'saved',
  a: 'applied',
  i: 'ignored',
};

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

export function useInboxShortcuts(handlers: ShortcutHandlers) {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey || event.altKey || isTypingTarget(event.target)) return;
      const current = handlersRef.current;
      const key = event.key.toLowerCase();

      if (key === 'j' || key === 'arrowdown') current.onMove(1);
      else if (key === 'k' || key === 'arrowup') current.onMove(-1);
      else if (key === 'o') current.onOpenApply();
      else if (key in STATUS_KEYS) current.onStatus(STATUS_KEYS[key]!);
      else return;
      event.preventDefault();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);
}
