"use client";

import { FormEvent, useEffect, useState } from "react";
import dynamic from "next/dynamic";
const API_URL = "http://127.0.0.1:8000";

/*
  IMPORTANT:
  Your MapComponent.tsx is inside the app folder.

  Therefore:
  ./MapComponent

  NOT:
  ./components/MapComponent
*/

const MapComponent = dynamic(
  () => import("./MapComponent"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[500px] items-center justify-center rounded-3xl border border-slate-200 bg-slate-100">
        <div className="text-sm font-medium text-slate-500">
          Loading map...
        </div>
      </div>
    ),
  }
);

/* =========================================================
   TYPES
========================================================= */

interface Competitor {
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
  address?: string;
  distance_km?: number;
  source?: string;
}

interface Weather {
  temperature?: number | null;
  humidity?: number | null;
  apparentTemperature?: number | null;
  precipitation?: number | null;
  windSpeed?: number | null;
  weatherCode?: number | null;
  available?: boolean;
}

interface MarketSignals {
  marketDemand: number;
  competition: number;
  profitPotential: number;
  marketOpportunity: number;
  risk: number;
}

interface AreaInsights {
  population?: string;
  populationScore?: number;
  purchasingPower?: string;
  purchasingPowerScore?: number;
  temperature?: number | null;
  humidity?: number | null;
  weatherAvailable?: boolean;
}

interface AnalysisResult {
  success: boolean;

  businessType: string;

  city: string;
  district: string;
  state: string;
  pincode: string;
  landmark?: string;
  nearestLandmark?: string;

  latitude: number;
  longitude: number;

  coordinates?: {
    latitude: number;
    longitude: number;
  };

  location?: {
    city: string;
    district: string;
    state: string;
    pincode: string;
    landmark?: string;
    latitude: number;
    longitude: number;
    formatted?: string;
  };

  feasibility: number;
  feasibilityScore: number;
  recommendation: string;

  marketSignals: MarketSignals;

  marketDemand?: number;
  competition?: number;
  profitPotential?: number;
  marketOpportunity?: number;
  risk?: number;

  areaInsights?: AreaInsights;

  weather?: Weather;

  competitors: Competitor[];
  competitorCount: number;

  aiRecommendation?: string;
  geminiRecommendation?: string;

  ai?: {
    provider?: string;
    model?: string;
    recommendation?: string;
  };

  apiStatus?: {
    geoapify?: boolean;
    olaMaps?: boolean;
    gemini?: boolean;
    weather?: boolean;
  };
}

/* =========================================================
   PAGE
========================================================= */

export default function HomePage() {
  /* =======================================================
     FORM STATE
  ======================================================= */

  const [businessType, setBusinessType] = useState("");
  const [city, setCity] = useState("");
  const [pincode, setPincode] = useState("");
  const [district, setDistrict] = useState("");
  const [state, setState] = useState("");
  const [landmark, setLandmark] = useState("");

  /* =======================================================
     UI STATE
  ======================================================= */

  const [detecting, setDetecting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const [result, setResult] =
    useState<AnalysisResult | null>(null);

  /* =======================================================
     BACKEND URL

     Your FastAPI is running on port 8000.
  ======================================================= */

  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";

  /* =======================================================
     PINCODE AUTO DETECTION

     User enters only pincode.
     Backend returns district + state.

     Example:
     700052
     -> North 24 Parganas
     -> West Bengal
  ======================================================= */

  useEffect(() => {
    const pin = pincode.replace(/\D/g, "");

    if (pin.length !== 6) {
      setDistrict("");
      setState("");
      return;
    }

    let cancelled = false;

    const detectPincode = async () => {
      setDetecting(true);
      setError("");

      try {
        const response = await fetch(
          `${API_BASE}/api/pincode/${pin}`,
          {
            method: "GET",
            headers: {
              Accept: "application/json",
            },
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            typeof data?.detail === "string"
              ? data.detail
              : "Unable to detect district and state."
          );
        }

        if (cancelled) return;

        /*
          IMPORTANT:
          Do not take city from this response.
          City / Village is entered manually by the user.
        */

        setDistrict(
          typeof data.district === "string"
            ? data.district
            : ""
        );

        setState(
          typeof data.state === "string"
            ? data.state
            : ""
        );

        setSuccessMessage(
          "District and state detected successfully."
        );
      } catch (err) {
        if (cancelled) return;

        setDistrict("");
        setState("");

        setError(
          err instanceof Error
            ? err.message
            : "Pincode detection failed."
        );
      } finally {
        if (!cancelled) {
          setDetecting(false);
        }
      }
    };

    detectPincode();

    return () => {
      cancelled = true;
    };
  }, [pincode]);

  /* =======================================================
     MANUAL PINCODE DETECT BUTTON
  ======================================================= */

  const handleDetect = async () => {
    const pin = pincode.replace(/\D/g, "");

    setError("");
    setSuccessMessage("");

    if (pin.length !== 6) {
      setError("Please enter a valid 6-digit pincode.");
      return;
    }

    setDetecting(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/pincode/${pin}`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : "Pincode could not be detected."
        );
      }

      setDistrict(data.district || "");
      setState(data.state || "");

      setSuccessMessage(
        `Detected: ${data.district || "Unknown district"}, ${
          data.state || "Unknown state"
        }`
      );
    } catch (err) {
      setDistrict("");
      setState("");

      setError(
        err instanceof Error
          ? err.message
          : "Pincode detection failed."
      );
    } finally {
      setDetecting(false);
    }
  };

  /* =======================================================
     ANALYZE BUSINESS
  ======================================================= */

  const handleAnalyze = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setError("");
    setSuccessMessage("");
    setResult(null);

    /* -------------------------------
       VALIDATION
    -------------------------------- */

    if (!businessType.trim()) {
      setError("Business type is required.");
      return;
    }

    if (!city.trim()) {
      setError("City / Village is required.");
      return;
    }

    const cleanPin = pincode.replace(/\D/g, "");

    if (cleanPin.length !== 6) {
      setError("Pincode must contain exactly 6 digits.");
      return;
    }

    /*
      Landmark is OPTIONAL.
      Therefore we DO NOT reject an empty landmark.
    */

    setAnalyzing(true);

    try {
      /*
        IMPORTANT:
        These names match your Pydantic backend model.

        businessType
        city
        pincode
        nearestLandmark

        No businessName.
      */

      const requestBody = {
        businessType: businessType.trim(),
        city: city.trim(),
        pincode: cleanPin,
        nearestLandmark: landmark.trim(),
      };

      console.log(
        "Sending analysis request:",
        requestBody
      );

      const response = await fetch(
        `${API_BASE}/api/analyze`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },

          body: JSON.stringify(requestBody),
        }
      );

      const data = await response.json();

      console.log(
        "Backend analysis response:",
        data
      );

      if (!response.ok) {
        /*
          FastAPI validation error.
        */

        if (Array.isArray(data?.detail)) {
          const messages = data.detail
            .map((item: any) => {
              if (
                typeof item === "string"
              ) {
                return item;
              }

              return (
                item?.msg ||
                item?.message ||
                "Invalid input"
              );
            })
            .filter(Boolean);

          throw new Error(
            messages.join(" | ")
          );
        }

        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : "Business analysis failed."
        );
      }

      if (!data || data.success !== true) {
        throw new Error(
          "Backend returned an invalid analysis response."
        );
      }

      /*
        Make absolutely sure competitors is an array.
        This prevents [object Object] problems.
      */

      const safeResult: AnalysisResult = {
        ...data,

        competitors: Array.isArray(
          data.competitors
        )
          ? data.competitors
          : [],

        competitorCount:
          typeof data.competitorCount ===
          "number"
            ? data.competitorCount
            : Array.isArray(
                data.competitors
              )
            ? data.competitors.length
            : 0,
      };

      setResult(safeResult);

      /*
        Scroll to report.
      */

      setTimeout(() => {
        document
          .getElementById("analysis-result")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (err) {
      console.error(
        "Analysis error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while analyzing the business."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  /* =======================================================
     START NEW ANALYSIS
  ======================================================= */

  const handleNewAnalysis = () => {
    setResult(null);
    setError("");
    setSuccessMessage("");

    setBusinessType("");
    setCity("");
    setPincode("");
    setDistrict("");
    setState("");
    setLandmark("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  /* =======================================================
     WEATHER DESCRIPTION
  ======================================================= */

  const getWeatherText = (
    code?: number | null
  ) => {
    if (code === undefined || code === null) {
      return "Not available";
    }

    if (code === 0) return "Clear sky";
    if (code <= 3) return "Partly cloudy";
    if (code <= 48) return "Foggy";
    if (code <= 57) return "Drizzle";
    if (code <= 67) return "Rain";
    if (code <= 77) return "Snow";
    if (code <= 82) return "Rain showers";
    if (code <= 86) return "Snow showers";
    return "Thunderstorm";
  };

  /* =======================================================
     SCORE HELPER
  ======================================================= */

  const scoreValue = (
    value: unknown
  ): number => {
    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return Math.max(
        0,
        Math.min(100, Math.round(value))
      );
    }

    return 0;
  };

  /* =======================================================
     SCORE BAR
  ======================================================= */

  const ScoreBar = ({
    value,
  }: {
    value: number;
  }) => {
    const safe = scoreValue(value);

    return (
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-slate-900 transition-all duration-700"
          style={{
            width: `${safe}%`,
          }}
        />
      </div>
    );
  };

  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-900">

      {/* ===================================================
          HEADER
      ================================================== */}

      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white shadow-lg">
              ✦
            </div>

            <div>
              <h1 className="text-base font-bold tracking-tight">
                HyperLocal AI
              </h1>

              <p className="text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400">
                Business Advisory
              </p>
            </div>

          </div>

          <div className="hidden rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-semibold text-slate-600 sm:block">
            AI Market Analysis
          </div>

        </div>
      </header>

      {/* ===================================================
          HERO / FORM
      ================================================== */}

      <section className="mx-auto max-w-7xl px-5 pb-14 pt-12 lg:px-8 lg:pt-16">

        <div className="mx-auto max-w-3xl text-center">

          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            AI-powered local feasibility analysis
          </div>

          <h2 className="text-4xl font-black tracking-tight text-slate-950 sm:text-5xl">
            Tell us about your business
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-slate-500">
            Enter your business type and local area details
            to generate an AI-powered feasibility report.
          </p>

        </div>

        {/* =================================================
            FORM CARD
        ================================================== */}

        <div className="mx-auto mt-10 max-w-4xl rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_20px_70px_rgba(15,23,42,0.08)] sm:p-8">

          <div className="mb-8 flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-950 text-lg text-white">
              01
            </div>

            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
                STEP 01 / ANALYZE
              </p>

              <h3 className="mt-1 text-xl font-bold">
                AI Market Analysis
              </h3>
            </div>

          </div>

          <form
            onSubmit={handleAnalyze}
            className="space-y-6"
          >

            {/* BUSINESS TYPE */}

            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700">
                Business Type <span className="text-red-500">*</span>
              </label>

              <input
                type="text"
                value={businessType}
                onChange={(e) =>
                  setBusinessType(
                    e.target.value
                  )
                }
                placeholder="e.g. Grocery Store"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm outline-none transition focus:border-slate-900 focus:bg-white focus:ring-4 focus:ring-slate-900/5"
              />
            </div>

            {/* CITY */}

            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700">
                City / Village{" "}
                <span className="text-red-500">*</span>
              </label>

              <input
                type="text"
                value={city}
                onChange={(e) =>
                  setCity(e.target.value)
                }
                placeholder="Enter city or village"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm outline-none transition focus:border-slate-900 focus:bg-white focus:ring-4 focus:ring-slate-900/5"
              />
            </div>

            {/* PINCODE */}

            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700">
                Pincode <span className="text-red-500">*</span>
              </label>

              <div className="flex flex-col gap-3 sm:flex-row">

                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={pincode}
                  onChange={(e) => {
                    const value =
                      e.target.value
                        .replace(/\D/g, "")
                        .slice(0, 6);

                    setPincode(value);
                    setSuccessMessage("");
                    setError("");
                  }}
                  placeholder="700052"
                  className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm font-medium outline-none transition focus:border-slate-900 focus:bg-white focus:ring-4 focus:ring-slate-900/5"
                />

                <button
                  type="button"
                  onClick={handleDetect}
                  disabled={
                    detecting ||
                    pincode.length !== 6
                  }
                  className="flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-6 py-4 text-sm font-bold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {detecting ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Detecting...
                    </>
                  ) : (
                    <>
                      ⌖ Detect
                    </>
                  )}
                </button>

              </div>

              <p className="mt-2 text-xs text-slate-400">
                Enter your 6-digit pincode. District and
                state will be detected automatically.
              </p>
            </div>

            {/* DISTRICT + STATE */}

            <div className="grid gap-4 sm:grid-cols-2">

              <div>
                <label className="mb-2 block text-sm font-bold text-slate-700">
                  District <span className="text-xs font-medium text-slate-400">• Auto</span>
                </label>

                <div className="flex min-h-[54px] items-center rounded-2xl border border-emerald-100 bg-emerald-50 px-4 text-sm font-semibold text-slate-700">
                  {district || "Will be detected from pincode"}
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-bold text-slate-700">
                  State <span className="text-xs font-medium text-slate-400">• Auto</span>
                </label>

                <div className="flex min-h-[54px] items-center rounded-2xl border border-emerald-100 bg-emerald-50 px-4 text-sm font-semibold text-slate-700">
                  {state || "Will be detected from pincode"}
                </div>
              </div>

            </div>

            {/* LANDMARK */}

            <div>
              <label className="mb-2 block text-sm font-bold text-slate-700">
                Nearest Landmark{" "}
                <span className="text-xs font-medium text-slate-400">
                  • Optional
                </span>
              </label>

              <input
                type="text"
                value={landmark}
                onChange={(e) =>
                  setLandmark(
                    e.target.value
                  )
                }
                placeholder="e.g. Airport Gate, Metro Station"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm outline-none transition focus:border-slate-900 focus:bg-white focus:ring-4 focus:ring-slate-900/5"
              />
            </div>

            {/* SUCCESS */}

            {successMessage && (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700">
                ✓ {successMessage}
              </div>
            )}

            {/* ERROR */}

            {error && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold leading-6 text-red-700">
                {error}
              </div>
            )}

            {/* ANALYZE BUTTON */}

            <button
              type="submit"
              disabled={analyzing}
              className="group flex w-full items-center justify-center gap-3 rounded-2xl bg-slate-950 px-6 py-4 text-sm font-bold text-white shadow-xl shadow-slate-950/10 transition hover:-translate-y-0.5 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {analyzing ? (
                <>
                  <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Analyzing Local Market...
                </>
              ) : (
                <>
                  ✦ Analyze Business Feasibility
                  <span className="transition group-hover:translate-x-1">
                    →
                  </span>
                </>
              )}
            </button>

          </form>
        </div>
      </section>

      {/* ===================================================
          RESULT
      ================================================== */}

      {result && (
        <section
          id="analysis-result"
          className="border-t border-slate-200 bg-white"
        >

          <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">

            {/* =================================================
                RESULT HEADER
            ================================================== */}

            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">

              <div>

                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
                  ✓ ANALYSIS COMPLETE
                </div>

                <h2 className="text-3xl font-black tracking-tight sm:text-4xl">
                  {result.businessType}
                </h2>

                <p className="mt-2 text-sm font-medium text-slate-500">
                  {result.city},{" "}
                  {result.district},{" "}
                  {result.state}
                </p>

                <p className="mt-1 text-xs font-bold uppercase tracking-wider text-slate-400">
                  PINCODE {result.pincode}
                </p>

              </div>

              {/* FEASIBILITY */}

              <div className="rounded-3xl border border-slate-200 bg-slate-50 px-7 py-5 text-center">

                <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-400">
                  Feasibility
                </p>

                <div className="mt-1 text-5xl font-black tracking-tight">
                  {scoreValue(
                    result.feasibilityScore ??
                      result.feasibility
                  )}
                </div>

                <p className="mt-1 text-xs font-semibold text-slate-400">
                  out of 100
                </p>

                <div className="mt-3 inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
                  ●{" "}
                  {result.recommendation ||
                    "GOOD OPPORTUNITY"}
                </div>

              </div>

            </div>

            {/* =================================================
                AI RECOMMENDATION
            ================================================== */}

            <div className="mt-8 rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-xl sm:p-8">

              <div className="flex items-start gap-4">

                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/10 text-xl">
                  ✦
                </div>

                <div className="min-w-0">

                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
                    AI RECOMMENDATION
                  </p>

                  <h3 className="mt-2 text-2xl font-black">
                    {result.recommendation}
                  </h3>

                  <p className="mt-3 text-sm leading-7 text-slate-300">
                    The AI system analyzed your selected
                    business and local market conditions
                    to generate this recommendation.
                  </p>

                </div>

              </div>

            </div>

            {/* =================================================
                LOCATION DETAILS
            ================================================== */}

            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

              <InfoCard
                label="City / Village"
                value={result.city}
              />

              <InfoCard
                label="District"
                value={result.district}
              />

              <InfoCard
                label="State"
                value={result.state}
              />

              <InfoCard
                label="Landmark"
                value={
                  result.landmark ||
                  result.nearestLandmark ||
                  "Not provided"
                }
              />

            </div>

            {/* =================================================
                MARKET SIGNALS
            ================================================== */}

            <div className="mt-12">

              <SectionHeading
                eyebrow="MARKET SIGNALS"
                title="Business feasibility signals"
                description="Key indicators generated from the local business analysis."
              />

              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">

                <ScoreCard
                  icon="⌁"
                  title="Market Demand"
                  subtitle="Estimated local demand"
                  value={
                    result.marketSignals
                      ?.marketDemand ?? 0
                  }
                />

                <ScoreCard
                  icon="◉"
                  title="Competition"
                  subtitle="Competitive pressure"
                  value={
                    result.marketSignals
                      ?.competition ?? 0
                  }
                />

                <ScoreCard
                  icon="₹"
                  title="Profit Potential"
                  subtitle="Expected earning potential"
                  value={
                    result.marketSignals
                      ?.profitPotential ?? 0
                  }
                />

                <ScoreCard
                  icon="↗"
                  title="Market Opportunity"
                  subtitle="Overall market opportunity"
                  value={
                    result.marketSignals
                      ?.marketOpportunity ?? 0
                  }
                />

                <ScoreCard
                  icon="!"
                  title="Risk"
                  subtitle="Estimated business risk"
                  value={
                    result.marketSignals
                      ?.risk ?? 0
                  }
                />

              </div>
            </div>

            {/* =================================================
                LOCAL INTELLIGENCE
            ================================================== */}

            <div className="mt-12">

              <SectionHeading
                eyebrow="LOCAL INTELLIGENCE"
                title="Area insights"
                description="Important information about your selected location."
              />

              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                <InsightCard
                  title="Population"
                  value={
                    result.areaInsights
                      ?.population ||
                    "Not available"
                  }
                  score={
                    result.areaInsights
                      ?.populationScore
                  }
                />

                <InsightCard
                  title="Purchasing Power"
                  value={
                    result.areaInsights
                      ?.purchasingPower ||
                    "Not available"
                  }
                  score={
                    result.areaInsights
                      ?.purchasingPowerScore
                  }
                />

                <InsightCard
                  title="Temperature"
                  value={
                    result.weather?.temperature !==
                    undefined &&
                    result.weather?.temperature !==
                      null
                      ? `${result.weather.temperature}°C`
                      : "Not available"
                  }
                />

                <InsightCard
                  title="Competitors"
                  value={`${result.competitorCount}`}
                  subtitle="Nearby businesses found"
                />

              </div>

            </div>

            {/* =================================================
                WEATHER
            ================================================== */}

            <div className="mt-12">

              <SectionHeading
                eyebrow="WEATHER"
                title="Current local weather"
                description="Weather data for the selected coordinates."
              />

              <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-6">

                {result.weather?.available ? (

                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">

                    <WeatherCard
                      icon="🌡"
                      label="Temperature"
                      value={
                        result.weather
                          .temperature != null
                          ? `${result.weather.temperature}°C`
                          : "N/A"
                      }
                    />

                    <WeatherCard
                      icon="💧"
                      label="Humidity"
                      value={
                        result.weather
                          .humidity != null
                          ? `${result.weather.humidity}%`
                          : "N/A"
                      }
                    />

                    <WeatherCard
                      icon="☁"
                      label="Condition"
                      value={getWeatherText(
                        result.weather
                          .weatherCode
                      )}
                    />

                    <WeatherCard
                      icon="🌧"
                      label="Precipitation"
                      value={
                        result.weather
                          .precipitation != null
                          ? `${result.weather.precipitation} mm`
                          : "N/A"
                      }
                    />

                    <WeatherCard
                      icon="💨"
                      label="Wind Speed"
                      value={
                        result.weather
                          .windSpeed != null
                          ? `${result.weather.windSpeed} km/h`
                          : "N/A"
                      }
                    />

                  </div>

                ) : (

                  <div className="rounded-2xl bg-white p-6 text-center text-sm font-medium text-slate-500">
                    Weather data is not available.
                  </div>

                )}

              </div>

            </div>

            {/* =================================================
                MAP + COMPETITORS
            ================================================== */}

            <div className="mt-12">

              <SectionHeading
                eyebrow="LOCAL COMPETITION"
                title="Nearby business landscape"
                description="Your selected location and nearby market area."
              />

              <div className="mt-6 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">

                <div className="p-4 sm:p-5">

                  <div className="mb-4 rounded-2xl bg-slate-50 p-4">

                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Market Area
                    </p>

                    <p className="mt-1 text-sm font-bold text-slate-800">
                      {result.city},{" "}
                      {result.district},{" "}
                      {result.state}
                    </p>

                  </div>

                  {Number.isFinite(
                    Number(result.latitude)
                  ) &&
                  Number.isFinite(
                    Number(result.longitude)
                  ) ? (

                    <MapComponent
                      latitude={Number(
                        result.latitude
                      )}
                      longitude={Number(
                        result.longitude
                      )}
                      competitors={
                        Array.isArray(
                          result.competitors
                        )
                          ? result.competitors
                          : []
                      }
                      competitorCount={
                        Number(
                          result.competitorCount
                        ) || 0
                      }
                    />

                  ) : (

                    <div className="flex h-[500px] items-center justify-center rounded-2xl bg-slate-100">
                      <p className="text-sm font-semibold text-slate-500">
                        Map coordinates are not available.
                      </p>
                    </div>

                  )}

                </div>

              </div>

            </div>

            {/* =================================================
                COMPETITOR LIST
            ================================================== */}

            <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">

              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
                    COMPETITORS
                  </p>

                  <h3 className="mt-1 text-2xl font-black">
                    Nearby businesses
                  </h3>
                </div>

                <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-bold text-slate-700">
                  {result.competitorCount} found
                </div>

              </div>

              {result.competitors.length > 0 ? (

                <div className="mt-6 grid gap-3 md:grid-cols-2">

                  {result.competitors
                    .slice(0, 12)
                    .map(
                      (
                        competitor,
                        index
                      ) => (

                        <div
                          key={`${competitor.name}-${competitor.latitude}-${competitor.longitude}-${index}`}
                          className="rounded-2xl border border-slate-100 bg-slate-50 p-4"
                        >

                          <div className="flex gap-3">

                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-lg shadow-sm">
                              🏪
                            </div>

                            <div className="min-w-0">

                              <h4 className="truncate text-sm font-bold text-slate-800">
                                {competitor.name ||
                                  "Nearby Business"}
                              </h4>

                              <p className="mt-1 text-xs text-slate-500">
                                {competitor.category ||
                                  "Business"}
                              </p>

                              {competitor.address && (
                                <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-400">
                                  {competitor.address}
                                </p>
                              )}

                              {typeof competitor.distance_km ===
                                "number" && (
                                <p className="mt-2 text-xs font-semibold text-slate-600">
                                  {competitor.distance_km.toFixed(
                                    2
                                  )}{" "}
                                  km away
                                </p>
                              )}

                            </div>

                          </div>

                        </div>

                      )
                    )}

                </div>

              ) : (

                <div className="mt-6 rounded-2xl bg-slate-50 p-6 text-center">

                  <p className="text-sm font-bold text-slate-700">
                    No nearby competitors returned.
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    The map will still show your selected
                    location.
                  </p>

                </div>

              )}

            </div>

            {/* =================================================
                GEMINI
            ================================================== */}

            <div className="mt-12">

              <SectionHeading
                eyebrow="GENERATIVE AI"
                title="Gemini business advisor"
                description="AI-generated insights based on your business and local market."
              />

              <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-xl sm:p-8">

                <div className="flex items-center justify-between gap-4">

                  <div className="flex items-center gap-3">

                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-xl">
                      ✦
                    </div>

                    <div>

                      <h3 className="font-bold">
                        AI Business Advisor
                      </h3>

                      <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
                        Powered by{" "}
                        {result.ai?.provider ||
                          "Gemini"}
                      </p>

                    </div>

                  </div>

                  {result.apiStatus?.gemini && (
                    <span className="rounded-full bg-emerald-400/10 px-3 py-1.5 text-xs font-bold text-emerald-300">
                      ● Connected
                    </span>
                  )}

                </div>

                <div className="mt-7">

                  {result.aiRecommendation ||
                  result.geminiRecommendation ||
                  result.ai?.recommendation ? (

                    <div className="whitespace-pre-wrap text-sm leading-7 text-slate-300">
                      {String(
                        result.aiRecommendation ||
                          result.geminiRecommendation ||
                          result.ai?.recommendation ||
                          ""
                      )}
                    </div>

                  ) : (

                    <p className="text-sm text-slate-400">
                      Gemini AI analysis is not available
                      for this result.
                    </p>

                  )}

                </div>

              </div>

            </div>

            {/* =================================================
                API STATUS
            ================================================== */}

            <div className="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-5">

              <div className="mb-4">
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
                  SYSTEM STATUS
                </p>

                <h3 className="mt-1 font-bold">
                  Data sources
                </h3>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

                <StatusItem
                  name="Geoapify"
                  active={
                    result.apiStatus?.geoapify
                  }
                />

                <StatusItem
                  name="Ola Maps"
                  active={
                    result.apiStatus?.olaMaps
                  }
                />

                <StatusItem
                  name="Gemini AI"
                  active={
                    result.apiStatus?.gemini
                  }
                />

                <StatusItem
                  name="Weather"
                  active={
                    result.apiStatus?.weather
                  }
                />

              </div>

            </div>

            {/* =================================================
                NEW ANALYSIS
            ================================================== */}

            <div className="mt-10 text-center">

              <button
                type="button"
                onClick={
                  handleNewAnalysis
                }
                className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
              >
                ← Start New Analysis
              </button>

            </div>

          </div>

        </section>
      )}

    </main>
  );
}

/* ===========================================================
   REUSABLE COMPONENTS
=========================================================== */

function InfoCard({
  label,
  value,
}: {
  label: string;
  value?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
        {label}
      </p>

      <p className="mt-2 break-words text-sm font-bold text-slate-800">
        {value || "Not available"}
      </p>

    </div>
  );
}

/* ===========================================================
   SCORE CARD
=========================================================== */

function ScoreCard({
  icon,
  title,
  subtitle,
  value,
}: {
  icon: string;
  title: string;
  subtitle: string;
  value: number;
}) {
  const safeValue = Math.max(
    0,
    Math.min(
      100,
      Math.round(
        Number.isFinite(
          Number(value)
        )
          ? Number(value)
          : 0
      )
    )
  );

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">

      <div className="flex items-start justify-between gap-3">

        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-lg">
          {icon}
        </div>

        <span className="text-2xl font-black">
          {safeValue}
        </span>

      </div>

      <h3 className="mt-5 text-sm font-bold text-slate-800">
        {title}
      </h3>

      <p className="mt-1 text-xs leading-5 text-slate-400">
        {subtitle}
      </p>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100">

        <div
          className="h-full rounded-full bg-slate-900"
          style={{
            width: `${safeValue}%`,
          }}
        />

      </div>

      <p className="mt-2 text-right text-[10px] font-bold uppercase tracking-wider text-slate-400">
        / 100
      </p>

    </div>
  );
}

/* ===========================================================
   SECTION HEADING
=========================================================== */

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div>

      <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">
        {eyebrow}
      </p>

      <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950 sm:text-3xl">
        {title}
      </h2>

      <p className="mt-2 text-sm leading-6 text-slate-500">
        {description}
      </p>

    </div>
  );
}

/* ===========================================================
   INSIGHT CARD
=========================================================== */

function InsightCard({
  title,
  value,
  score,
  subtitle,
}: {
  title: string;
  value: string;
  score?: number;
  subtitle?: string;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">

      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
        {title}
      </p>

      <p className="mt-3 break-words text-base font-black text-slate-800">
        {value}
      </p>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-400">
          {subtitle}
        </p>
      )}

      {typeof score === "number" && (
        <div className="mt-4">

          <div className="flex justify-between text-xs font-bold text-slate-400">
            <span>Indicator</span>
            <span>{score}/100</span>
          </div>

          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">

            <div
              className="h-full rounded-full bg-slate-900"
              style={{
                width: `${Math.max(
                  0,
                  Math.min(100, score)
                )}%`,
              }}
            />

          </div>

        </div>
      )}

    </div>
  );
}

/* ===========================================================
   WEATHER CARD
=========================================================== */

function WeatherCard({
  icon,
  label,
  value,
}: {
  icon: string;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">

      <div className="flex items-center gap-3">

        <span className="text-xl">
          {icon}
        </span>

        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
          {label}
        </span>

      </div>

      <p className="mt-4 text-lg font-black text-slate-800">
        {value}
      </p>

    </div>
  );
}

/* ===========================================================
   STATUS ITEM
=========================================================== */

function StatusItem({
  name,
  active,
}: {
  name: string;
  active?: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">

      <span className="text-sm font-semibold text-slate-700">
        {name}
      </span>

      <span
        className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${
          active
            ? "bg-emerald-100 text-emerald-700"
            : "bg-red-100 text-red-600"
        }`}
      >
        {active
          ? "CONNECTED"
          : "UNAVAILABLE"}
      </span>

    </div>
  );
}
