import clsx from 'clsx';
import type { ReactNode } from 'react';
import { BullMark } from '@/components/ui/BullMark';
import { ContourBackground } from '@/components/ui/Contour';

const SYSTEM_NAME = 'Sistema de Verificação de Dados Alimentícios Bovinos';
const TAGLINE = 'Tecnologia que alimenta dados, inteligência que fortalece o campo.';

interface AuthLayoutProps {
  title: string;
  /** Shorter hero on small screens, for long forms. */
  compact?: boolean;
  children: ReactNode;
}

/** Shared shell of the login and sign-up pages: brand on one side, form on the other. */
export function AuthLayout({ title, compact = false, children }: AuthLayoutProps) {
  return (
    <main className="relative isolate min-h-dvh overflow-hidden">
      <ContourBackground />
      <div className="mx-auto grid min-h-dvh max-w-7xl items-center gap-8 px-5 py-8 sm:px-10 lg:grid-cols-[1.15fr_0.85fr] lg:gap-20 lg:py-16">
        <section aria-label="SVDA" className="grid max-w-2xl content-center gap-3 lg:gap-5">
          <BullMark className={clsx('text-moss', compact ? 'w-12 lg:w-20' : 'w-14 lg:w-20')} />
          <h1 className="font-display text-[clamp(4.75rem,13vw,10.5rem)] leading-[0.85] font-extrabold tracking-[-0.045em] text-moss">
            SVDA
          </h1>
          <p className={clsx('text-sm font-semibold text-grass', compact && 'hidden sm:block')}>
            {SYSTEM_NAME}
          </p>
          <p
            className={clsx(
              'max-w-[20ch] font-display text-[clamp(1.5rem,3.2vw,2.5rem)] leading-[1.1] font-semibold tracking-tight text-balance',
              compact && 'hidden sm:block',
            )}
          >
            {TAGLINE}
          </p>
        </section>

        <section
          aria-labelledby="auth-title"
          className="w-full max-w-lg justify-self-center rounded-[2rem] bg-white/90 p-6 shadow-[0_24px_60px_-24px_rgba(34,64,46,0.35)] backdrop-blur-md sm:p-10"
        >
          <h2
            id="auth-title"
            className="mb-6 font-display text-[clamp(2rem,4vw,2.75rem)] leading-none font-bold tracking-tight text-moss"
          >
            {title}
          </h2>
          {children}
        </section>
      </div>
    </main>
  );
}
