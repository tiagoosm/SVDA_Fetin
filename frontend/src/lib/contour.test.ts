import { describe, expect, it } from 'vitest';
import { contourPolygons } from './contour';

const base = {
  width: 100,
  height: 100,
  hills: [{ x: 0.5, y: 0.5, scale: 1 }],
  levels: 7,
  step: 6.2,
};

describe('contourPolygons', () => {
  it('is deterministic for a seed', () => {
    expect(contourPolygons({ ...base, seed: 'abc' })).toEqual(
      contourPolygons({ ...base, seed: 'abc' }),
    );
  });

  it('draws a different terrain for a different seed', () => {
    expect(contourPolygons({ ...base, seed: 'abc' })).not.toEqual(
      contourPolygons({ ...base, seed: 'abd' }),
    );
  });

  it('draws one polygon per level and hill', () => {
    const polygons = contourPolygons({
      ...base,
      seed: 'x',
      levels: 4,
      hills: [
        { x: 0.2, y: 0.2, scale: 1 },
        { x: 0.8, y: 0.8, scale: 1 },
      ],
    });
    expect(polygons).toHaveLength(8);
  });

  it('honors the number of points', () => {
    const [polygon] = contourPolygons({ ...base, seed: 'x', points: 30 });
    expect(polygon?.split(' ')).toHaveLength(30);
  });
});
