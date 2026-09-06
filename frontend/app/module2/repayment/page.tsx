import { PageContainer } from "@/components/module2/ui/PageContainer";
import { StepIndicator } from "@/components/module2/StepIndicator";
import { RepaymentRiskView } from "@/components/module2/repayment/RepaymentRiskView";

export default function RepaymentPage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <div className="mb-8 rounded-lg border border-border bg-surface p-6">
          <StepIndicator currentStepId="repayment" />
        </div>
        <RepaymentRiskView />
      </PageContainer>
    </main>
  );
}