import { cn } from "@/lib/utils";

type BadgeTone = "positive" | "warning" | "neutral";

interface BadgeProps {
  label: string;
  tone?: BadgeTone;
}

const toneStyles: Record<BadgeTone, string> = {
  positive: "bg-emerald/10 text-emerald border-emerald/20",
  warning: "bg-amber/10 text-amber border-amber/20",
  neutral: "bg-navy/5 text-navy/70 border-border",
};

export function Badge({ label, tone = "neutral" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-2.5 py-1 text-xs font-medium font-body",
        toneStyles[tone]
      )}
    >
      {label}
    </span>
  );
}