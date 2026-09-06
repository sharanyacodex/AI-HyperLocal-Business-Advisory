interface ScoreRingProps {
  score: number;
  label: string;
  sublabel: string;
}

export function ScoreRing({ score, label, sublabel }: ScoreRingProps) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circumference - (clamped / 100) * circumference;
  const tone = clamped >= 70 ? "#10B981" : clamped >= 45 ? "#F59E0B" : "#DB8B09";

  return (
    <div className="relative flex h-44 w-44 shrink-0 items-center justify-center">
      <svg viewBox="0 0 160 160" className="h-full w-full -rotate-90">
        <circle cx="80" cy="80" r={radius} fill="none" stroke="#E2E8F0" strokeWidth="10" />
        <circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke={tone}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center text-center">
        <span className="text-[11px] uppercase tracking-wide text-navy/40 font-body">
          {label}
        </span>
        <span className="font-heading text-4xl font-semibold text-navy tabular-figures">
          {Math.round(clamped)}
          <span className="text-lg font-normal text-navy/40">/100</span>
        </span>
        <span className="text-xs text-navy/50 font-body">{sublabel}</span>
      </div>
    </div>
  );
}