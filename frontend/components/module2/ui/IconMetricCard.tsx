import { LucideIcon } from "lucide-react";

type AccentColor = "blue" | "orange" | "teal" | "purple" | "emerald";

interface IconMetricCardProps {
  icon: LucideIcon;
  value: string;
  unitLabel?: string;
  label: string;
  sublabel?: string;
  progressPercent: number;
  accent: AccentColor;
}

const accentStyles: Record<AccentColor, { bg: string; bar: string; icon: string }> = {
  blue: { bg: "bg-accentBlue/10", bar: "bg-accentBlue", icon: "text-accentBlue" },
  orange: { bg: "bg-accentOrange/10", bar: "bg-accentOrange", icon: "text-accentOrange" },
  teal: { bg: "bg-accentTeal/10", bar: "bg-accentTeal", icon: "text-accentTeal" },
  purple: { bg: "bg-accentPurple/10", bar: "bg-accentPurple", icon: "text-accentPurple" },
  emerald: { bg: "bg-emerald/10", bar: "bg-emerald", icon: "text-emerald" },
};

export function IconMetricCard({
  icon: Icon,
  value,
  unitLabel,
  label,
  sublabel,
  progressPercent,
  accent,
}: IconMetricCardProps) {
  const styles = accentStyles[accent];

  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <div className="flex items-start justify-between">
        <span className={`flex h-9 w-9 items-center justify-center rounded ${styles.bg}`}>
          <Icon className={`h-4 w-4 ${styles.icon}`} />
        </span>
        <span className="font-heading text-xl font-semibold text-navy tabular-figures">
          {value}
          {unitLabel && (
            <span className="ml-1 text-xs font-normal text-navy/40 font-body">
              {unitLabel}
            </span>
          )}
        </span>
      </div>

      <p className="mt-4 text-sm font-medium text-navy font-body">{label}</p>
      {sublabel && <p className="text-xs text-navy/50 font-body">{sublabel}</p>}

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-border">
        <div
          className={`h-full rounded-full ${styles.bar}`}
          style={{ width: `${Math.max(0, Math.min(100, progressPercent))}%` }}
        />
      </div>
    </div>
  );
}