import clsx from 'clsx';
import { useMemo } from 'react';
import { contourPolygons } from '@/lib/contour';

const BACKGROUNDS = {
  light: {
    options: {
      seed: 'svda-light',
      width: 1600,
      height: 1000,
      hills: [
        { x: 0.22, y: 0.3, scale: 1 },
        { x: 0.82, y: 0.74, scale: 0.85 },
      ],
      levels: 16,
      step: 44,
    },
    stroke: '#5f8f46',
    opacity: 0.3,
    strokeWidth: 1.4,
  },
  dark: {
    options: {
      seed: 'svda-dark',
      width: 900,
      height: 1400,
      hills: [
        { x: 0.2, y: 0.18, scale: 0.9 },
        { x: 0.85, y: 0.82, scale: 1 },
      ],
      levels: 14,
      step: 46,
    },
    stroke: '#9cc58a',
    opacity: 0.2,
    strokeWidth: 1.3,
  },
} as const;

interface ContourBackgroundProps {
  variant?: keyof typeof BACKGROUNDS;
  className?: string;
}

/** Full-bleed topographic map used behind pages and the sidebar. */
export function ContourBackground({ variant = 'light', className }: ContourBackgroundProps) {
  const config = BACKGROUNDS[variant];
  const polygons = useMemo(() => contourPolygons(config.options), [config]);
  return (
    <svg
      viewBox={`0 0 ${config.options.width} ${config.options.height}`}
      preserveAspectRatio="xMidYMid slice"
      fill="none"
      stroke={config.stroke}
      strokeOpacity={config.opacity}
      strokeWidth={config.strokeWidth}
      strokeLinejoin="round"
      aria-hidden="true"
      className={clsx('pointer-events-none absolute inset-0 -z-10 size-full', className)}
    >
      {polygons.map((points, index) => (
        <polygon key={index} points={points} />
      ))}
    </svg>
  );
}

interface ContourThumbProps {
  /** Each seed draws its own terrain, so every conversation looks different. */
  seed: string;
  className?: string;
}

export function ContourThumb({ seed, className }: ContourThumbProps) {
  const polygons = useMemo(
    () =>
      contourPolygons({
        seed,
        width: 100,
        height: 100,
        hills: [{ x: 0.5, y: 0.5, scale: 1 }],
        levels: 7,
        step: 6.2,
        points: 90,
      }),
    [seed],
  );
  return (
    <svg
      viewBox="0 0 100 100"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinejoin="round"
      aria-hidden="true"
      className={clsx('size-full', className)}
    >
      {polygons.map((points, index) => (
        <polygon key={index} points={points} />
      ))}
    </svg>
  );
}
