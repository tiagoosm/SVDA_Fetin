import { BullMark } from '@/components/ui/BullMark';

export function LoadingScreen() {
  return (
    <div role="status" className="grid min-h-dvh place-items-center bg-field text-moss">
      <div className="flex flex-col items-center gap-3">
        <BullMark decorative className="w-16 motion-safe:animate-pulse" />
        <p className="font-medium">Carregando…</p>
      </div>
    </div>
  );
}
