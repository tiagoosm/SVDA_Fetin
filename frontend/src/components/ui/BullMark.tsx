import clsx from 'clsx';
import bull from '@/assets/bull.png';

interface BullMarkProps {
  className?: string;
  /** Decorative marks are hidden from assistive technology. */
  decorative?: boolean;
}

/** The SVDA bull, drawn as a mask so it takes the current text color. */
export function BullMark({ className, decorative = false }: BullMarkProps) {
  const mask = `url(${bull})`;
  return (
    <span
      role={decorative ? undefined : 'img'}
      aria-label={decorative ? undefined : 'Touro, símbolo do SVDA'}
      aria-hidden={decorative || undefined}
      className={clsx('inline-block aspect-[1023/775] bg-current', className)}
      style={{
        WebkitMaskImage: mask,
        maskImage: mask,
        WebkitMaskSize: 'contain',
        maskSize: 'contain',
        WebkitMaskRepeat: 'no-repeat',
        maskRepeat: 'no-repeat',
        WebkitMaskPosition: 'center',
        maskPosition: 'center',
      }}
    />
  );
}
