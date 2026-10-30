import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { typeInto } from './typewriter';

function element(html: string) {
  const div = document.createElement('div');
  div.innerHTML = html;
  return div;
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe('typeInto', () => {
  it('reveals the text a few characters at a time and keeps the markup', () => {
    const div = element('<p>Olá <strong>mundo</strong>!</p>');
    typeInto(div, { charsPerTick: 3, tickMs: 10 });

    expect(div.querySelector('strong')).not.toBeNull();
    expect(div.textContent).toBe('Olá');

    vi.advanceTimersByTime(10);
    expect(div.textContent).toBe('Olá mu');
    vi.runAllTimers();
    expect(div.textContent).toBe('Olá mundo!');
    expect(div.innerHTML).toBe('<p>Olá <strong>mundo</strong>!</p>');
  });

  it('reports progress on every step', () => {
    const onProgress = vi.fn();
    typeInto(element('<p>abcdefgh</p>'), { charsPerTick: 4, tickMs: 10, onProgress });
    vi.runAllTimers();
    expect(onProgress).toHaveBeenCalledTimes(2);
  });

  it('shows the full text when cancelled', () => {
    const div = element('<p>texto completo</p>');
    const cancel = typeInto(div, { charsPerTick: 2, tickMs: 10 });
    expect(div.textContent).toBe('te');
    cancel();
    expect(div.textContent).toBe('texto completo');
    vi.runAllTimers();
    expect(div.textContent).toBe('texto completo');
  });
});
