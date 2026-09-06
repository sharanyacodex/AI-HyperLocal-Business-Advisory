import { PageContainer } from "@/components/module2/ui/PageContainer";
import { StepIndicator } from "@/components/module2/StepIndicator";
import { RecommendationView } from "@/components/module2/recommendation/RecommendationView";

export default function RecommendationPage() {
  return (
    <main className="min-h-screen bg-background">
      <PageContainer>
        <div className="mb-8 rounded-lg border border-border bg-surface p-6">
          <StepIndicator currentStepId="recommendation" />
        </div>
        <RecommendationView />
      </PageContainer>
    </main>
  );
}