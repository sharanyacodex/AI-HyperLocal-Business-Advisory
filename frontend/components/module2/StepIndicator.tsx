import { cn } from "@/lib/utils";
import { MODULE2_FLOW_STEPS } from "@/types/module2/flow";

interface StepIndicatorProps {
  currentStepId: string;
}

export function StepIndicator({ currentStepId }: StepIndicatorProps) {
  const currentIndex = MODULE2_FLOW_STEPS.findIndex(
    (step) => step.id === currentStepId
  );

  return (
    <ol className="flex w-full flex-col gap-3 sm:flex-row sm:items-center sm:gap-0">
      {MODULE2_FLOW_STEPS.map((step, index) => {
        const isComplete = index < currentIndex;
        const isCurrent = index === currentIndex;

        return (
          <li key={step.id} className="flex flex-1 items-center">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium font-body",
                  isComplete && "border-emerald bg-emerald text-white",
                  isCurrent && "border-emerald text-emerald",
                  !isComplete && !isCurrent && "border-border text-navy/40"
                )}
              >
                {index + 1}
              </span>
              <span
                className={cn(
                  "text-sm font-body whitespace-nowrap",
                  isCurrent ? "text-navy font-medium" : "text-navy/50"
                )}
              >
                {step.label}
              </span>
            </div>
            {index < MODULE2_FLOW_STEPS.length - 1 && (
              <span
                className={cn(
                  "mx-3 hidden h-px flex-1 sm:block",
                  isComplete ? "bg-emerald" : "bg-border"
                )}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}