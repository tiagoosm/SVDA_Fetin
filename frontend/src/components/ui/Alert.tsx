import clsx from 'clsx';
import type { ReactNode } from 'react';

interface AlertProps {
  tone: 'error' | 'info';
  children: ReactNode;
  className?: string;
}

/** Inline feedback. Errors are announced immediately; info is polite. */
export function Alert({ tone, children, className }: AlertProps) {
  return (
    <p
      role={tone === 'error' ? 'alert' : 'status'}
      className={clsx(
        'rounded-2xl px-4 py-3 text-sm font-medium',
        tone === 'error' ? 'bg-red-50 text-red-800' : 'bg-sky text-moss',
        className,
      )}
    >
      {children}
    </p>
  );
}
