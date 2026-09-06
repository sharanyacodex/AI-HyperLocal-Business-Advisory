import { PageContainer } from "@/components/module2/ui/PageContainer";
import { SectionHeading } from "@/components/module2/ui/SectionHeading";
import { StepIndicator } from "@/components/module2/StepIndicator";
import { FinancialResultsView } from "@/components/module2/results/FinancialResultsView";

export default function FinancialResultsPage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <div className="mb-8 rounded-lg border border-border bg-surface p-6">
          <StepIndicator currentStepId="financial" />
        </div>

        <SectionHeading
          title="Financial feasibility"
          description="Based on the details you provided."
        />

        <FinancialResultsView />
      </PageContainer>
    </main>
  );
}