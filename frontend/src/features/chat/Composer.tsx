import { useState } from 'react';
import type { FormEvent } from 'react';
import { SendIcon } from '@/components/ui/icons';
import { DISCLAIMER } from './welcome';

export const MAX_MESSAGE_LENGTH = 2000;

interface ComposerProps {
  disabled: boolean;
  onSend: (text: string) => void;
}

export function Composer({ disabled, onSend }: ComposerProps) {
  const [text, setText] = useState('');

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
  }

  return (
    <div className="px-3.5 pt-2 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:px-[clamp(1rem,5vw,4.5rem)]">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 rounded-full bg-white p-1.5 pl-2 shadow-[0_14px_36px_-14px_rgba(34,64,46,0.5)]"
      >
        <label htmlFor="message" className="sr-only">
          Sua dúvida
        </label>
        <input
          id="message"
          type="text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={MAX_MESSAGE_LENGTH}
          autoComplete="off"
          placeholder="Tire sua dúvida..."
          className="min-h-12 min-w-0 flex-1 rounded-full bg-transparent px-4 text-base text-ink placeholder:text-muted/70 focus-visible:outline-offset-[-2px] focus-visible:outline-sun"
        />
        <button
          type="submit"
          disabled={disabled || text.trim() === ''}
          aria-label="Enviar"
          className="grid size-13 shrink-0 place-items-center rounded-full bg-sun text-moss transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <SendIcon />
        </button>
      </form>
      <p className="mt-2 text-center text-xs text-muted sm:text-[0.8125rem]">{DISCLAIMER}</p>
    </div>
  );
}
