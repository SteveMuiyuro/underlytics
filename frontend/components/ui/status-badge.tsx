import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type StatusTone =
  | "neutral"
  | "indigo"
  | "cyan"
  | "green"
  | "amber"
  | "red"
  | "slate";

const toneClasses: Record<StatusTone, string> = {
  neutral: "border-slate-200 bg-slate-100 text-slate-700",
  indigo: "border-indigo-200 bg-indigo-50 text-indigo-700",
  cyan: "border-cyan-200 bg-cyan-50 text-cyan-700",
  green: "border-emerald-200 bg-emerald-50 text-emerald-700",
  amber: "border-amber-200 bg-amber-50 text-amber-700",
  red: "border-rose-200 bg-rose-50 text-rose-700",
  slate: "border-slate-300 bg-slate-900 text-white",
};

interface StatusBadgeProps {
  children: React.ReactNode;
  tone?: StatusTone;
  className?: string;
}

export function StatusBadge({
  children,
  tone = "neutral",
  className,
}: StatusBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "h-7 rounded-full px-3 text-[11px] font-semibold tracking-[0.16em] uppercase",
        toneClasses[tone],
        className
      )}
    >
      {children}
    </Badge>
  );
}
