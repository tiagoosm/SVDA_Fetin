/**
 * Contour lines ("curvas de nível") drawn as nested wobbly polygons.
 * Deterministic: the same seed always produces the same terrain, which is how each
 * conversation gets its own small map.
 */

export interface Hill {
  /** Center, as a fraction of the width/height. */
  x: number;
  y: number;
  scale: number;
}

export interface ContourOptions {
  seed: string;
  width: number;
  height: number;
  hills: readonly Hill[];
  levels: number;
  /** Radius added by each level, in viewBox units. */
  step: number;
  /** Points per polygon (smoothness). */
  points?: number;
}

function hashSeed(seed: string): number {
  let hash = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    hash ^= seed.charCodeAt(i);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash;
}

/** Small seeded PRNG (mulberry32). */
function random(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Returns one `points` attribute value per contour line. */
export function contourPolygons(options: ContourOptions): string[] {
  const { seed, width, height, hills, levels, step, points = 120 } = options;
  const next = random(hashSeed(seed));
  const polygons: string[] = [];

  for (const hill of hills) {
    const phases = Array.from({ length: 5 }, () => next() * Math.PI * 2);
    const amplitudes = Array.from({ length: 5 }, (_, i) => (0.05 + next() * 0.07) / (i + 1));

    for (let level = 1; level <= levels; level++) {
      const radius = level * step * hill.scale;
      const coordinates: string[] = [];
      for (let j = 0; j < points; j++) {
        const angle = (2 * Math.PI * j) / points;
        let wobble = 1;
        for (let i = 0; i < 5; i++) {
          wobble +=
            (amplitudes[i] ?? 0) * Math.sin((i + 2) * angle + (phases[i] ?? 0) + level * 0.15);
        }
        const r = radius * wobble;
        const x = hill.x * width + r * Math.cos(angle) * 1.25;
        const y = hill.y * height + r * Math.sin(angle) * 0.85;
        coordinates.push(`${x.toFixed(0)},${y.toFixed(0)}`);
      }
      polygons.push(coordinates.join(' '));
    }
  }
  return polygons;
}
