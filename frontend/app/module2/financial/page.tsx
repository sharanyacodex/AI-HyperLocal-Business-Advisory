import { PageContainer } from "@/components/module2/ui/PageContainer";
import { Card } from "@/components/module2/ui/Card";
import { SectionHeading } from "@/components/module2/ui/SectionHeading";
import { StepIndicator } from "@/components/module2/StepIndicator";
import { BusinessInputForm } from "@/components/module2/financial/BusinessInputForm";

export default function FinancialInputPage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <div className="mb-8 rounded-lg border border-border bg-surface p-6">
          <StepIndicator currentStepId="business" />
        </div>

        <Card>
          <SectionHeading
            title="Business & financial details"
            description="This helps us work out your loan requirement and repayment capacity."
          />
          <BusinessInputForm />
        </Card>
      </PageContainer>
    </main>
  );
}