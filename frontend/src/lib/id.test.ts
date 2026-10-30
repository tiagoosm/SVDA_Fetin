import { afterEach, describe, expect, it, vi } from 'vitest';
import { uuid } from './id';

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

afterEach(() => vi.unstubAllGlobals());

describe('uuid', () => {
  it('returns a v4 UUID', () => {
    expect(uuid()).toMatch(UUID_V4);
  });

  it('still works where crypto.randomUUID is unavailable (insecure contexts)', () => {
    const real = globalThis.crypto;
    vi.stubGlobal('crypto', {
      getRandomValues: (array: Uint8Array) => real.getRandomValues(array),
    });
    const id = uuid();
    expect(id).toMatch(UUID_V4);
    expect(uuid()).not.toBe(id);
  });
});
