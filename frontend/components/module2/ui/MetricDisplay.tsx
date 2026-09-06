interface MetricDisplayProps {
  label: string;
  value: string;
  sublabel?: string;
  tone?: "default" | "positive" | "warning";
}

const toneStyles: Record<NonNullable<MetricDisplayProps["tone"]>, string> = {
  default: "text-navy",
  positive: "text-emerald",
  warning: "text-amber",
};

export function MetricDisplay({
  label,
  value,
  sublabel,
  tone = "default",
}: MetricDisplayProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-navy/60 font-body">{label}</span>
      <span
        className={`text-3xl font-semibold font-heading tabular-figures ${toneStyles[tone]}`}
      >
        {value}
      </span>
      {sublabel && (
        <span className="text-xs text-navy/50 font-body">{sublabel}</span>
      )}
    </div>
  );
}