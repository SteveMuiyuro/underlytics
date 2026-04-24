import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  className?: string;
  indicatorClassName?: string;
}

export function Progress({
  value,
  className,
  indicatorClassName,
}: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div
      className={cn(
        "h-3 w-full overflow-hidden rounded-full bg-slate-200/80",
        className
      )}
      aria-valuemax={100}
      aria-valuemin={0}
      aria-valuenow={clamped}
      role="progressbar"
    >
      <div
        className={cn(
          "h-full rounded-full bg-slate-950 transition-[width] duration-500 ease-out",
          indicatorClassName
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
