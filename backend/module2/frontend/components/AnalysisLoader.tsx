import { Loader2 } from "lucide-react";

export default function AnalysisLoader({ step }: { step: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 text-center">
      <Loader2 className="animate-spin text-skyaccent" size={36} strokeWidth={1.5} />
      <p className="mt-6 font-display text-2xl italic text-navy">
        Analyzing your business…
      </p>
      <p className="mt-2 text-sm text-navy/50">{step}</p>
    </div>
  );
}
