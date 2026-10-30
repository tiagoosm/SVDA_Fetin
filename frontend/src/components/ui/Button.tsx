import clsx from 'clsx';
import type { ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'accent';

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-moss text-white hover:bg-moss-light',
  secondary: 'bg-transparent text-moss ring-2 ring-inset ring-moss hover:bg-moss/5',
  accent: 'bg-sun text-moss hover:brightness-95',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ variant = 'primary', className, type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={clsx(
        'inline-flex min-h-13 w-full items-center justify-center gap-2 rounded-full px-7 text-lg font-bold transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-60',
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}
