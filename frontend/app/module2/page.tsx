import Link from "next/link";
import { PageContainer } from "@/components/module2/ui/PageContainer";
import { Button } from "@/components/module2/ui/Button";
import { StepIndicator } from "@/components/module2/StepIndicator";
import { MODULE2_FLOW_STEPS } from "@/types/module2/flow";

export default function Module2LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <div className="mb-10">
          <h1 className="text-2xl font-semibold text-navy sm:text-3xl">
            Business Advisory
          </h1>
          <p className="mt-2 max-w-xl text-sm text-navy/60 font-body sm:text-base">
            Answer a few questions about your business and we&apos;ll work out
            what it costs to run, what you can borrow, how safely you can
            repay it, and which government schemes you may qualify for.
          </p>
        </div>

        <div className="mb-10 rounded-lg border border-border bg-surface p-6">
          <StepIndicator currentStepId="business" />
        </div>

        <div className="mb-10 divide-y divide-border rounded-lg border border-border bg-surface">
          {MODULE2_FLOW_STEPS.map((step, index) => (
            <div key={step.id} className="flex items-start gap-4 p-5">
              <span className="mt-0.5 text-sm font-medium text-navy/40 font-body">
                {index + 1}
              </span>
              <div>
                <p className="text-sm font-medium text-navy font-body">
                  {step.label}
                </p>
                <p className="mt-0.5 text-sm text-navy/50 font-body">
                  {stepDescriptions[step.id]}
                </p>
              </div>
            </div>
          ))}
        </div>

        <Link href="/module2/financial">
          <Button variant="primary">Start assessment</Button>
        </Link>
      </PageContainer>
    </main>
  );
}

const stepDescriptions: Record<string, string> = {
  business: "Tell us about your business, location, and finances.",
  financial: "See your project cost, own contribution, and loan requirement.",
  repayment: "Check your EMI, surplus, and repayment risk level.",
  schemes: "View government schemes you may be eligible for.",
  recommendation: "Get a clear summary and final recommendation.",
};
