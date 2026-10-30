import { describe, expect, it } from 'vitest';
import { plainText } from './text';

describe('plainText', () => {
  it('removes emphasis marks', () => {
    expect(plainText('Cerca de **16% de proteína** e __65%__')).toBe(
      'Cerca de 16% de proteína e 65%',
    );
  });

  it('keeps the text of links and drops list and heading markers', () => {
    expect(plainText('## Dieta\n- [Embrapa](https://x.y)\n- sal mineral')).toBe(
      'Dieta Embrapa sal mineral',
    );
  });

  it('collapses whitespace', () => {
    expect(plainText('a\n\n  b')).toBe('a b');
  });
});
