import { PageContainer } from "@/components/module2/ui/PageContainer";
import { StepIndicator } from "@/components/module2/StepIndicator";
import { SchemeListView } from "@/components/module2/schemes/SchemeListView";

export default function SchemesPage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <div className="mb-8 rounded-lg border border-border bg-surface p-6">
          <StepIndicator currentStepId="schemes" />
        </div>
        <SchemeListView />
      </PageContainer>
    </main>
  );
}