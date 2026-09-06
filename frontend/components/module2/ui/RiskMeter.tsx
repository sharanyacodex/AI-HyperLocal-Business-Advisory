import { cn } from "@/lib/utils";
import { RepaymentRiskLevel, RISK_LEVEL_LABELS } from "@/types/module2/repayment";

interface RiskMeterProps {
  level: RepaymentRiskLevel;
}

const levelOrder: RepaymentRiskLevel[] = ["low", "moderate", "high"];

const levelColor: Record<RepaymentRiskLevel, string> = {
  low: "bg-emerald",
  moderate: "bg-amber",
  high: "bg-amber-hover",
};

export function RiskMeter({ level }: RiskMeterProps) {
  const activeIndex = levelOrder.indexOf(level);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-1.5">
        {levelOrder.map((item, index) => (
          <span
            key={item}
            className={cn(
              "h-2 flex-1 rounded-full",
              index <= activeIndex ? levelColor[level] : "bg-border"
            )}
          />
        ))}
      </div>
      <span
        className={cn(
          "text-sm font-medium font-body",
          level === "low" && "text-emerald",
          level === "moderate" && "text-amber",
          level === "high" && "text-amber-hover"
        )}
      >
        {RISK_LEVEL_LABELS[level]}
      </span>
    </div>
  );
}