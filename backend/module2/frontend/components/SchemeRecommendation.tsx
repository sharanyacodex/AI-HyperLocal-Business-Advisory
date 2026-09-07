import type { SchemeRecommendationResponse } from "@/lib/types";

export default function SchemeRecommendation({
  recommendation,
}: {
  recommendation: SchemeRecommendationResponse;
}) {
  return (
    <div className="glass rounded-2xl p-7">
      <p className="text-sm text-navy/55">Scheme recommendation</p>
      <p className="mt-1 font-display text-2xl text-navy">
        {recommendation.recommended_scheme_name ?? "No single scheme selected"}
      </p>
      <p className="mt-3 text-sm leading-relaxed text-navy/65">
        {recommendation.recommendation_reason}
      </p>
    </div>
  );
}
