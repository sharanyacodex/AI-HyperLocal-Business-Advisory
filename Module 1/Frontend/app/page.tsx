"use client";

import dynamic from "next/dynamic";
import { useRef, useState } from "react";

const MapComponent = dynamic(() => import("./MapComponent"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[500px] items-center justify-center rounded-3xl border border-slate-200 bg-slate-50">
      <div className="text-center">
        <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-slate-300 border-t-slate-900" />
        <p className="text-sm font-medium text-slate-500">
          Loading competitor map...
        </p>
      </div>
    </div>
  ),
});

interface Competitor {
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
  address?: string;
  distance_m?: number;
  place_id?: string;
}

interface AnalysisResult {
  success?: boolean;
  business_type?: string;
  pincode?: string;
  location_name?: string;
  district?: string;
  state?: string;
  country?: string;
  searched_location?: string;

  latitude?: number;
  longitude?: number;

  market_demand?: number;
  market_data_source?: string;

  population_density?: number;
  population_density_actual?: number;
  population_data_source?: string;
  population_estimate?: number;

  purchasing_power?: number;
  purchasing_power_proxy?: number | null;
  purchasing_power_level?: string | null;
  purchasing_power_data_source?: string | null;

  competitor_count?: number;
  competition_level?: number;
  competitor_data_availability?: string;

  opportunity?: number;
  profit_potential?: number;

  risk_safety?: number;
  risk_data_source?: string;

  current_weather?: {
    temperature_c?: number;
    wind_speed_kmh?: number;
    precipitation_mm?: number;
    weather_code?: number;
    data_source?: string;
  };

  feasibility?:
    | number
    | {
        feasibility_score?: number;
        score?: number;
        recommendation?: string;
      };

  competitors?: Competitor[];
  message?: string;
}

const API_BASE_URL = "http://127.0.0.1:8000";

const PINCODE_TIMEOUT = 8000;

/*
  Main competitor search radius.

  IMPORTANT:
  This frontend sends 10 km to the backend.
  The backend must also actually use this value
  when querying the location APIs.
*/
const COMPETITOR_RADIUS_KM = 10;

/* =========================================================
   MAIN PAGE
========================================================= */

export default function Home() {
  const [businessType, setBusinessType] = useState("");

  /*
    Village / City is MANUAL.
    It is intentionally NOT populated from PIN lookup.
  */
  const [villageCity, setVillageCity] = useState("");

  /*
    District and State are automatically populated
    from the PIN code.
  */
  const [district, setDistrict] = useState("");
  const [state, setState] = useState("");

  /*
    Optional manual landmark.
    This gives the backend additional location context.
  */
  const [landmark, setLandmark] = useState("");

  const [pincode, setPincode] = useState("");

  const [result, setResult] =
    useState<AnalysisResult | null>(null);

  const [mapLatitude, setMapLatitude] =
    useState<number | null>(null);

  const [mapLongitude, setMapLongitude] =
    useState<number | null>(null);

  const [loading, setLoading] = useState(false);

  const [locationLoading, setLocationLoading] =
    useState(false);

  const [error, setError] = useState("");

  const resolvedPincodeRef =
    useRef<string>("");

  const resolvedCoordinatesRef =
    useRef<{
      latitude: number;
      longitude: number;
    } | null>(null);

  const pincodeRequestRef =
    useRef<AbortController | null>(null);

  /* =========================================================
     PINCODE LOOKUP

     PIN lookup ONLY updates:
       - District
       - State
       - Coordinates

     It DOES NOT update Village / City.
  ========================================================= */

  const lookupPincode = async (
    cleanValue: string
  ) => {
    if (pincodeRequestRef.current) {
      pincodeRequestRef.current.abort();
    }

    const controller =
      new AbortController();

    pincodeRequestRef.current =
      controller;

    const timeoutId = setTimeout(() => {
      controller.abort();
    }, PINCODE_TIMEOUT);

    setLocationLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/pincode?pincode=${encodeURIComponent(
          cleanValue
        )}`,
        {
          method: "GET",
          signal: controller.signal,
          cache: "no-store",
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(
          `Pincode API returned ${response.status}`
        );
      }

      const data =
        await response.json();

      console.log(
        "PINCODE RESPONSE:",
        data
      );

      if (!data.success) {
        resolvedPincodeRef.current =
          "";

        resolvedCoordinatesRef.current =
          null;

        setError(
          data.message ||
            "PIN code not found."
        );

        return null;
      }

      /*
        We intentionally ignore location_name
        for Village / City.

        The PIN API may return a postal-office name,
        which is NOT necessarily the exact village/city
        where the user wants to analyse the business.
      */

      const resolvedDistrict =
        data.district ||
        data.location?.district ||
        "";

      const resolvedState =
        data.state ||
        data.location?.state ||
        "";

      const latitude = Number(
        data.latitude ??
          data.location?.latitude
      );

      const longitude = Number(
        data.longitude ??
          data.location?.longitude
      );

      if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
      ) {
        resolvedPincodeRef.current =
          "";

        resolvedCoordinatesRef.current =
          null;

        setError(
          "PIN code was found, but coordinates are unavailable."
        );

        return null;
      }

      resolvedPincodeRef.current =
        cleanValue;

      resolvedCoordinatesRef.current = {
        latitude,
        longitude,
      };

      /*
        CORRECT BEHAVIOUR:
        District -> automatic
        State    -> automatic
        Village  -> manual, untouched
      */

      setDistrict(
        resolvedDistrict
      );

      setState(
        resolvedState
      );

      setMapLatitude(latitude);
      setMapLongitude(longitude);

      return {
        success: true,
        latitude,
        longitude,
        district:
          resolvedDistrict,
        state:
          resolvedState,
      };
    } catch (err: unknown) {
      clearTimeout(timeoutId);

      if (
        err instanceof DOMException &&
        err.name === "AbortError"
      ) {
        /*
          Don't show an error for an old request
          that was intentionally cancelled because
          the user entered another digit.
        */

        if (
          pincodeRequestRef.current ===
          controller
        ) {
          setError(
            "Pincode service is taking too long. Please try again."
          );
        }
      } else {
        console.error(
          "PINCODE ERROR:",
          err
        );

        setError(
          "Could not connect to the pincode service. Make sure FastAPI is running on port 8000."
        );
      }

      resolvedPincodeRef.current =
        "";

      resolvedCoordinatesRef.current =
        null;

      return null;
    } finally {
      clearTimeout(timeoutId);

      if (
        pincodeRequestRef.current ===
        controller
      ) {
        setLocationLoading(false);
      }
    }
  };

  /* =========================================================
     PINCODE CHANGE

     PIN automatically resolves:
       District
       State
       Coordinates

     Village / City remains manual.
  ========================================================= */

  const handlePincodeChange = async (
    value: string
  ) => {
    const cleanValue =
      value
        .replace(/\D/g, "")
        .slice(0, 6);

    setPincode(cleanValue);
    setError("");

    resolvedPincodeRef.current =
      "";

    resolvedCoordinatesRef.current =
      null;

    setMapLatitude(null);
    setMapLongitude(null);

    if (pincodeRequestRef.current) {
      pincodeRequestRef.current.abort();
      pincodeRequestRef.current =
        null;
    }

    /*
      Do NOT clear Village / City here.

      The user owns this field.
    */

    if (cleanValue.length !== 6) {
      setDistrict("");
      setState("");

      return;
    }

    await lookupPincode(
      cleanValue
    );
  };

  /* =========================================================
     ANALYZE BUSINESS
  ========================================================= */

  const handleAnalyze = async () => {
    setError("");

    if (!businessType.trim()) {
      setError(
        "Please enter a business type."
      );
      return;
    }

    if (!villageCity.trim()) {
      setError(
        "Please enter your Village / City."
      );
      return;
    }

    if (!/^\d{6}$/.test(
      pincode.trim()
    )) {
      setError(
        "Please enter a valid 6-digit PIN code."
      );
      return;
    }

    if (!district.trim()) {
      setError(
        "District could not be resolved from the PIN code."
      );
      return;
    }

    if (!state.trim()) {
      setError(
        "State could not be resolved from the PIN code."
      );
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      let coordinates =
        resolvedCoordinatesRef.current;

      /*
        If the PIN lookup has not completed,
        resolve it now.

        Notice that we DO NOT replace villageCity
        with anything returned by the PIN API.
      */

      if (
        !coordinates ||
        resolvedPincodeRef.current !==
          pincode.trim()
      ) {
        console.log(
          "PIN not resolved yet. Looking up PIN..."
        );

        const pincodeData =
          await lookupPincode(
            pincode.trim()
          );

        if (!pincodeData) {
          setLoading(false);
          return;
        }

        coordinates = {
          latitude:
            pincodeData.latitude,

          longitude:
            pincodeData.longitude,
        };
      }

      if (!coordinates) {
        setError(
          "Could not get coordinates for this PIN code."
        );

        return;
      }

      const {
        latitude,
        longitude,
      } = coordinates;

      console.log(
        "USING COORDINATES:",
        latitude,
        longitude
      );

      console.log(
        "USER LOCATION:",
        {
          villageCity,
          district,
          state,
          landmark,
          pincode,
        }
      );

      setMapLatitude(latitude);
      setMapLongitude(longitude);

      /*
        =====================================================
        IMPORTANT

        Send the user's actual manual location details
        to the backend.

        PIN:
          gives coordinates / geographic reference

        Village / City:
          user's exact textual location

        Landmark:
          additional location clue

        District / State:
          automatically resolved from PIN
      =====================================================
      */

      const params =
        new URLSearchParams();

      params.set(
        "latitude",
        String(latitude)
      );

      params.set(
        "longitude",
        String(longitude)
      );

      params.set(
        "business_type",
        businessType.trim()
      );

      params.set(
        "village_city",
        villageCity.trim()
      );

      params.set(
        "district",
        district.trim()
      );

      params.set(
        "state",
        state.trim()
      );

      params.set(
        "pincode",
        pincode.trim()
      );

      /*
        Optional landmark.
        Empty landmark is allowed.
      */

      if (landmark.trim()) {
        params.set(
          "landmark",
          landmark.trim()
        );
      }

      /*
        Explicit 10 km search radius.
      */

      params.set(
        "radius_km",
        String(COMPETITOR_RADIUS_KM)
      );

      console.log(
        "Calling /module1/analyze with:",
        params.toString()
      );

      const analyzeResponse =
        await fetch(
          `${API_BASE_URL}/module1/analyze?${params.toString()}`,
          {
            method: "GET",
            cache: "no-store",
          }
        );

      if (!analyzeResponse.ok) {
        throw new Error(
          `Analysis API returned ${analyzeResponse.status}`
        );
      }

      const analyzeData =
        await analyzeResponse.json();

      console.log(
        "ANALYSIS DATA:",
        analyzeData
      );

      if (!analyzeData.success) {
        setError(
          analyzeData.message ||
            "Business analysis failed."
        );

        return;
      }

      const competitors: Competitor[] =
        Array.isArray(
          analyzeData.competitors
        )
          ? analyzeData.competitors
          : [];

      /*
        IMPORTANT:
        searched_location now represents
        the user's manual location.

        We do NOT use the PIN API's
        location_name here.
      */

      const searchedLocation =
        [
          villageCity.trim(),
          district.trim(),
          state.trim(),
        ]
          .filter(Boolean)
          .join(", ");

      const finalResult:
        AnalysisResult = {
          ...analyzeData,

          pincode:
            pincode.trim(),

          /*
            Keep user's manually entered
            Village / City.
          */

          location_name:
            villageCity.trim(),

          district:
            district.trim(),

          state:
            state.trim(),

          latitude,
          longitude,

          searched_location:
            searchedLocation,

          competitors,

          competitor_count:
            typeof analyzeData.competitor_count ===
            "number"
              ? analyzeData.competitor_count
              : competitors.length,
        };

      setResult(
        finalResult
      );
    } catch (err) {
      console.error(
        "ANALYSIS ERROR:",
        err
      );

      setError(
        "Could not connect to backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <main className="min-h-screen overflow-hidden bg-[#f7f8fc] text-slate-900">

      {/* HEADER */}

      <section className="relative overflow-hidden bg-slate-950">

        <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 animate-pulse rounded-full bg-cyan-500/20 blur-3xl" />

        <div className="pointer-events-none absolute -right-32 top-10 h-96 w-96 animate-pulse rounded-full bg-violet-500/20 blur-3xl" />

        <div className="pointer-events-none absolute bottom-0 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-blue-500/10 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-6 py-20 lg:px-8">

          <div className="mx-auto max-w-4xl text-center">

            <div className="mb-7 inline-flex animate-[pulse_3s_ease-in-out_infinite] items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-300 backdrop-blur">

              <span className="h-2 w-2 animate-ping rounded-full bg-emerald-400" />

              AI-Powered Local Business Intelligence

            </div>

            <h1 className="text-4xl font-black tracking-tight text-white sm:text-6xl lg:text-7xl">

              Turn your business idea

              <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">

                into a smarter decision.

              </span>

            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">

              Analyze market demand, competition,
              opportunity, profit potential and
              local risk — all in one place.

            </p>

          </div>

        </div>

      </section>

      {/* MAIN */}

      <div className="relative mx-auto -mt-8 max-w-7xl px-6 pb-16 lg:px-8">

        {/* INPUT CARD */}

        <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_25px_80px_-25px_rgba(15,23,42,0.25)] sm:p-8 lg:p-10">

          <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">

            <div>

              <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                Business analysis
              </p>

              <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                Tell us about your business
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Enter your business idea, location
                and 6-digit Indian PIN code.
              </p>

            </div>

            <div className="rounded-full bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-500">
              Takes less than a minute
            </div>

          </div>

          {/* INPUT GRID */}

          <div className="grid gap-5 md:grid-cols-2">

            {/* BUSINESS TYPE */}

            <InputField
              label="Business Type"
              required
            >

              <input
                type="text"
                value={businessType}
                onChange={(e) =>
                  setBusinessType(
                    e.target.value
                  )
                }
                placeholder="e.g. Dairy, Bakery, Cafe"
                className={inputClass}
              />

            </InputField>

            {/* PIN CODE */}

            <InputField
              label="PIN Code"
              required
            >

              <div className="relative">

                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={pincode}
                  onChange={(e) =>
                    handlePincodeChange(
                      e.target.value
                    )
                  }
                  placeholder="e.g. 722122"
                  className={`${inputClass} pr-12`}
                />

                {locationLoading && (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2">

                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />

                  </div>
                )}

              </div>

              {locationLoading && (
                <p className="mt-2 text-xs font-medium text-blue-600">
                  Finding district and state...
                </p>
              )}

              {pincode.length === 6 &&
                !locationLoading &&
                district &&
                state && (
                  <p className="mt-2 text-xs font-medium text-emerald-600">
                    ✓ District and state found
                  </p>
                )}

            </InputField>

            {/* VILLAGE / CITY - MANUAL */}

            <InputField
              label="Village / City"
              required
            >

              <input
                type="text"
                value={villageCity}
                onChange={(e) =>
                  setVillageCity(
                    e.target.value
                  )
                }
                placeholder="Enter village or city manually"
                className={inputClass}
              />

              <p className="mt-2 text-xs text-slate-400">
                Enter the exact village, town or city
                where you want to start the business.
              </p>

            </InputField>

            {/* DISTRICT - AUTO */}

            <InputField label="District">

              <input
                type="text"
                value={district}
                readOnly
                placeholder="Automatically filled from PIN"
                className={`${inputClass} cursor-not-allowed bg-slate-100 text-slate-600`}
              />

              <p className="mt-2 text-xs text-emerald-600">
                Automatically detected from PIN code
              </p>

            </InputField>

            {/* STATE - AUTO */}

            <InputField label="State">

              <input
                type="text"
                value={state}
                readOnly
                placeholder="Automatically filled from PIN"
                className={`${inputClass} cursor-not-allowed bg-slate-100 text-slate-600`}
              />

              <p className="mt-2 text-xs text-emerald-600">
                Automatically detected from PIN code
              </p>

            </InputField>

            {/* NEAREST LANDMARK - MANUAL */}

            <InputField label="Nearest Landmark">

              <input
                type="text"
                value={landmark}
                onChange={(e) =>
                  setLandmark(
                    e.target.value
                  )
                }
                placeholder="e.g. near school, market, railway station"
                className={inputClass}
              />

              <p className="mt-2 text-xs text-slate-400">
                Optional, but recommended for better
                location matching.
              </p>

            </InputField>

          </div>

          {/* HOW IT WORKS */}

          <div className="mt-7 rounded-2xl border border-blue-100 bg-blue-50/60 p-5">

            <div className="flex gap-4">

              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-lg text-white shadow-lg shadow-blue-600/20">
                ✦
              </div>

              <div>

                <p className="font-semibold text-slate-800">
                  How it works
                </p>

                <p className="mt-1 text-sm leading-6 text-slate-600">

                  PIN code automatically provides the
                  district, state and geographic
                  coordinates. You manually provide the
                  exact Village / City and optional nearest
                  landmark. The system then uses these
                  details to search for local businesses
                  within a 10 km area.

                </p>

              </div>

            </div>

          </div>

          {/* ERROR */}

          {error && (

            <div className="mt-5 flex items-center gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">

              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-red-100">
                !
              </span>

              {error}

            </div>

          )}

          {/* ANALYZE */}

          <button
            onClick={handleAnalyze}
            disabled={
              loading ||
              locationLoading
            }
            className="group mt-7 flex w-full items-center justify-center gap-3 rounded-2xl bg-slate-950 px-6 py-4 text-sm font-bold text-white shadow-xl shadow-slate-900/20 transition duration-300 hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-blue-600/20 disabled:cursor-not-allowed disabled:opacity-60"
          >

            {loading ? (
              <>

                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />

                Analyzing your business...

              </>
            ) : locationLoading ? (
              <>

                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />

                Finding location...

              </>
            ) : (
              <>

                Analyze Business

                <span className="text-lg transition-transform duration-300 group-hover:translate-x-1">
                  →
                </span>

              </>
            )}

          </button>

        </div>

        {/* =================================================
            RESULTS
        ================================================= */}

        {result && (

          <div className="mt-8 space-y-8">

            {/* RESULT TOP */}

            <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_25px_80px_-30px_rgba(15,23,42,0.2)]">

              <div className="border-b border-slate-100 p-6 sm:p-8">

                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">

                  <div>

                    <div className="mb-2 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-emerald-600">
                      Analysis complete
                    </div>

                    <h2 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
                      Feasibility Result
                    </h2>

                    <p className="mt-2 text-slate-500">

                      {result.business_type ||
                        businessType}{" "}

                      <span className="text-slate-300">
                        •
                      </span>{" "}

                      {result.searched_location ||
                        villageCity}

                    </p>

                  </div>

                  <div className="rounded-2xl bg-slate-50 px-5 py-3">

                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      PIN Code
                    </p>

                    <p className="mt-1 text-lg font-bold text-slate-800">
                      {result.pincode ||
                        pincode}
                    </p>

                  </div>

                </div>

              </div>

              {/* SCORE + SUMMARY */}

              <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[auto_1fr] lg:items-center">

                <div className="flex justify-center">

                  <FeasibilityCircle
                    score={getFeasibilityScore(
                      result
                    )}
                  />

                </div>

                <div>

                  <p className="text-sm font-bold uppercase tracking-wider text-slate-400">
                    Recommendation
                  </p>

                  <h3 className="mt-2 text-3xl font-black tracking-tight text-slate-900">
                    {getRecommendation(
                      result
                    )}
                  </h3>

                  <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">

                    This score combines market demand,
                    local competition, business
                    opportunity, profit potential and
                    local risk/safety.

                  </p>

                  <div className="mt-6 grid gap-3 sm:grid-cols-3">

                    <MiniStat
                      label="Location"
                      value={
                        result.location_name ||
                        villageCity ||
                        "--"
                      }
                    />

                    <MiniStat
                      label="District"
                      value={
                        result.district ||
                        district ||
                        "--"
                      }
                    />

                    <MiniStat
                      label="State"
                      value={
                        result.state ||
                        state ||
                        "--"
                      }
                    />

                  </div>

                  {landmark.trim() && (
                    <div className="mt-3">
                      <MiniStat
                        label="Nearest Landmark"
                        value={landmark}
                      />
                    </div>
                  )}

                </div>

              </div>

            </div>

            {/* BUSINESS SIGNALS */}

            <div>

              <div className="mb-5">

                <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                  Business signals
                </p>

                <h3 className="mt-1 text-2xl font-bold text-slate-900">
                  Your business at a glance
                </h3>

              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">

                <ScoreCard
                  title="Market Demand"
                  value={
                    result.market_demand
                  }
                  description={
                    result.market_data_source ||
                    "Market analysis"
                  }
                  icon="↗"
                  type="positive"
                />

                {/* POPULATION DENSITY */}

                <ScoreCard
                  title="Population Density"
                  value={
                    result.population_density_actual ??
                    result.population_density
                  }
                  description="People per km²"
                  icon="👥"
                  type="population"
                  showBar={false}
                  suffix={
                    result.population_density_actual
                      ? " people/km²"
                      : "/100"
                  }
                />

                {/* PURCHASING POWER */}

                <ScoreCard
                  title="Purchasing Power"
                  value={
                    result.purchasing_power
                  }
                  description={
                    result.purchasing_power_data_source ||
                    "Local purchasing power indicator"
                  }
                  icon="₹"
                  type="purchasing"
                  status={getPurchasingPowerStatus(
                    result
                  )}
                />

                <ScoreCard
                  title="Competition"
                  value={
                    result.competition_level
                  }
                  description={
                    result.competitor_data_availability ===
                    "LIMITED"
                      ? "Limited competitor data"
                      : "Local competition"
                  }
                  icon="◎"
                  type="competition"
                />

                <ScoreCard
                  title="Opportunity"
                  value={
                    result.opportunity
                  }
                  description="Market opportunity"
                  icon="✦"
                  type="positive"
                />

                <ScoreCard
                  title="Profit Potential"
                  value={
                    result.profit_potential
                  }
                  description="Estimated potential"
                  icon="₹"
                  type="profit"
                />

                <ScoreCard
                  title="Risk Safety"
                  value={
                    result.risk_safety
                  }
                  description={
                    result.risk_data_source ||
                    "Risk assessment"
                  }
                  icon="✓"
                  type="safety"
                />

                <ScoreCard
                  title="Competitors"
                  value={
                    result.competitor_count
                  }
                  description="Businesses found within 10 km"
                  icon="⌖"
                  showBar={false}
                  type="competition"
                />

              </div>

            </div>

            {/* WEATHER DASHBOARD */}

            {result.current_weather && (

              <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">

                <div className="mb-6">

                  <p className="text-sm font-semibold uppercase tracking-wider text-cyan-600">
                    Environmental intelligence
                  </p>

                  <h3 className="mt-1 text-2xl font-bold text-slate-900">
                    Current Weather
                  </h3>

                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                  {/* WEATHER STATUS */}

                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">

                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Condition
                    </p>

                    <p className="mt-3 text-2xl font-black text-slate-900">
                      {getWeatherCondition(
                        result.current_weather.weather_code
                      )}
                    </p>

                  </div>

                  {/* TEMPERATURE */}

                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">

                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Temperature
                    </p>

                    <p className="mt-3 text-2xl font-black text-slate-900">

                      {result.current_weather
                        .temperature_c !== undefined
                        ? `${result.current_weather.temperature_c}°C`
                        : "--"}

                    </p>

                  </div>

                  {/* WIND */}

                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">

                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Wind Speed
                    </p>

                    <p className="mt-3 text-2xl font-black text-slate-900">

                      {result.current_weather
                        .wind_speed_kmh !== undefined
                        ? `${result.current_weather.wind_speed_kmh} km/h`
                        : "--"}

                    </p>

                  </div>

                  {/* PRECIPITATION */}

                  <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">

                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Precipitation
                    </p>

                    <p className="mt-3 text-2xl font-black text-slate-900">

                      {result.current_weather
                        .precipitation_mm !== undefined
                        ? `${result.current_weather.precipitation_mm} mm`
                        : "--"}

                    </p>

                  </div>

                </div>

                <div className="mt-4 rounded-2xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white p-5">

                  <p className="text-sm font-semibold text-slate-700">
                    Weather Assessment
                  </p>

                  <p className="mt-1 text-sm text-slate-500">

                    Current local condition is{" "}

                    <span className="font-bold text-slate-800">
                      {getWeatherCondition(
                        result.current_weather.weather_code
                      )}
                    </span>
                    .

                  </p>

                  {result.current_weather.data_source && (
                    <p className="mt-2 text-xs font-medium text-slate-400">
                      Source:{" "}
                      {result.current_weather.data_source}
                    </p>
                  )}

                </div>

              </div>

            )}

            {/* MAP */}

            {mapLatitude !== null &&
              mapLongitude !== null && (

                <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">

                  <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">

                    <div>

                      <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                        Local intelligence
                      </p>

                      <h3 className="mt-1 text-2xl font-bold text-slate-900">
                        Nearby Competitors
                      </h3>

                      <p className="mt-1 text-sm text-slate-500">
                        Businesses found within{" "}
                        {COMPETITOR_RADIUS_KM} km of
                        your selected location.
                      </p>

                    </div>

                    <div className="rounded-full bg-slate-100 px-4 py-2 text-xs font-bold text-slate-600">

                      {result.competitor_count ??
                        0}{" "}
                      businesses found

                    </div>

                  </div>

                  <MapComponent
                    latitude={
                      mapLatitude
                    }
                    longitude={
                      mapLongitude
                    }
                    competitors={
                      Array.isArray(
                        result.competitors
                      )
                        ? result.competitors
                        : []
                    }
                  />

                </div>

              )}

            {/* COMPETITOR DETAILS */}

            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">

              <div className="mb-6">

                <p className="text-sm font-semibold uppercase tracking-wider text-violet-600">
                  Market landscape
                </p>

                <h3 className="mt-1 text-2xl font-bold text-slate-900">
                  Competitor Details
                </h3>

              </div>

              {Array.isArray(
                result.competitors
              ) &&
              result.competitors.length >
                0 ? (

                <div className="grid gap-4 md:grid-cols-2">

                  {result.competitors.map(
                    (
                      competitor: Competitor,
                      index: number
                    ) => (

                      <div
                        key={`${competitor.name}-${competitor.latitude}-${competitor.longitude}-${index}`}
                        className="group rounded-2xl border border-slate-200 bg-slate-50 p-5 transition duration-300 hover:-translate-y-1 hover:border-blue-200 hover:bg-white hover:shadow-lg"
                      >

                        <div className="flex items-start justify-between gap-4">

                          <div className="flex min-w-0 gap-3">

                            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-lg text-white">
                              ⌂
                            </div>

                            <div className="min-w-0">

                              <p className="truncate font-bold text-slate-800">
                                {competitor.name ||
                                  "Nearby Business"}
                              </p>

                              {competitor.category && (
                                <p className="mt-1 text-xs font-medium text-blue-600">
                                  {competitor.category}
                                </p>
                              )}

                            </div>

                          </div>

                          {typeof competitor.distance_m ===
                            "number" && (

                            <span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-600 shadow-sm">

                              {(
                                competitor.distance_m /
                                1000
                              ).toFixed(2)}{" "}
                              km

                            </span>

                          )}

                        </div>

                        {competitor.address && (

                          <p className="mt-4 text-sm leading-6 text-slate-500">
                            {competitor.address}
                          </p>

                        )}

                      </div>

                    )
                  )}

                </div>

              ) : (

                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">

                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-2xl shadow-sm">
                    ⌖
                  </div>

                  <p className="mt-4 font-bold text-slate-700">
                    No competitors found
                  </p>

                  <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">

                    No matching businesses were
                    returned within the selected
                    10 km search area.

                  </p>

                  {result.competitor_data_availability ===
                    "LIMITED" && (

                    <p className="mt-3 text-xs font-semibold text-amber-600">

                      Competitor data availability is
                      currently limited.

                    </p>

                  )}

                </div>

              )}

            </div>

            {/* RISK & SAFETY */}

            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">

              <div className="mb-6">

                <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
                  Environmental intelligence
                </p>

                <h3 className="mt-1 text-2xl font-bold text-slate-900">
                  Risk & Safety
                </h3>

              </div>

              <div className="grid gap-4 sm:grid-cols-2">

                <div className="rounded-2xl bg-slate-50 p-5">

                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Risk Safety Score
                  </p>

                  <p className="mt-3 text-4xl font-black text-slate-900">

                    {result.risk_safety ??
                      "--"}

                    <span className="ml-1 text-lg font-medium text-slate-400">
                      /100
                    </span>

                  </p>

                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">

                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                      style={{
                        width: `${clamp(
                          Number(
                            result.risk_safety ??
                              0
                          )
                        )}%`,
                      }}
                    />

                  </div>

                </div>

                <div className="rounded-2xl bg-slate-50 p-5">

                  <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Data Source
                  </p>

                  <p className="mt-3 text-xl font-bold text-slate-800">
                    {result.risk_data_source ||
                      "Not available"}
                  </p>

                  <p className="mt-2 text-sm text-slate-500">
                    Weather and local safety
                    assessment.
                  </p>

                </div>

              </div>

            </div>

          </div>

        )}

      </div>

    </main>
  );
}

/* =========================================================
   INPUT CLASS
========================================================= */

const inputClass =
  "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-sm font-medium text-slate-900 outline-none transition duration-200 placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10";

/* =========================================================
   INPUT FIELD
========================================================= */

function InputField({
  label,
  required = false,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>

      <label className="mb-2 block text-sm font-bold text-slate-700">

        {label}

        {required && (
          <span className="ml-1 text-blue-600">
            *
          </span>
        )}

      </label>

      {children}

    </div>
  );
}

/* =========================================================
   SCORE CARD
========================================================= */

function ScoreCard({
  title,
  value,
  description,
  icon,
  showBar = true,
  type = "positive",
  status,
  suffix,
}: {
  title: string;
  value:
    | number
    | string
    | null
    | undefined;
  description: string;
  icon: string;
  showBar?: boolean;
  type?:
    | "positive"
    | "competition"
    | "profit"
    | "safety"
    | "population"
    | "purchasing";
  status?: string;
  suffix?: string;
}) {
  const numericValue =
    typeof value === "number"
      ? value
      : Number(value);

  const safeValue =
    Number.isFinite(
      numericValue
    )
      ? numericValue
      : 0;

  let iconClass =
    "bg-blue-50 text-blue-600";

  let barClass =
    "bg-blue-600";

  if (type === "profit") {
    iconClass =
      "bg-violet-50 text-violet-600";

    barClass =
      "bg-violet-600";
  }

  if (type === "safety") {
    iconClass =
      "bg-emerald-50 text-emerald-600";

    barClass =
      "bg-emerald-500";
  }

  if (type === "competition") {
    iconClass =
      "bg-orange-50 text-orange-600";

    barClass =
      "bg-orange-500";
  }

  if (type === "population") {
    iconClass =
      "bg-indigo-50 text-indigo-600";

    barClass =
      "bg-indigo-600";
  }

  if (type === "purchasing") {
    iconClass =
      "bg-amber-50 text-amber-600";

    barClass =
      "bg-amber-500";
  }

  return (
    <div className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-xl">

      <div className="flex items-start justify-between">

        <div
          className={`flex h-11 w-11 items-center justify-center rounded-xl text-lg font-bold ${iconClass}`}
        >
          {icon}
        </div>

        <div className="text-right">

          <p className="text-2xl font-black text-slate-900">

            {value ?? "--"}

            {suffix && (
              <span className="ml-1 text-sm font-bold text-slate-400">
                {suffix}
              </span>
            )}

          </p>

          {showBar &&
            typeof value ===
              "number" && (

              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                /100
              </p>

            )}

        </div>

      </div>

      <h4 className="mt-5 font-bold text-slate-800">
        {title}
      </h4>

      <p className="mt-1 text-xs leading-5 text-slate-500">
        {description}
      </p>

      {status && (
        <div className="mt-4">

          <span className="inline-flex rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700">
            {status}
          </span>

        </div>
      )}

      {showBar && (

        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">

          <div
            className={`h-full rounded-full ${barClass} transition-all duration-700 ease-out`}
            style={{
              width: `${clamp(
                safeValue
              )}%`,
            }}
          />

        </div>

      )}

    </div>
  );
}

/* =========================================================
   MINI STAT
========================================================= */

function MiniStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">

      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
        {label}
      </p>

      <p className="mt-1 truncate text-sm font-bold text-slate-700">
        {value}
      </p>

    </div>
  );
}

/* =========================================================
   FEASIBILITY CIRCLE
========================================================= */

function FeasibilityCircle({
  score,
}: {
  score:
    | number
    | string
    | null
    | undefined;
}) {
  const numericScore =
    typeof score === "number"
      ? score
      : Number(score);

  const safeScore =
    Number.isFinite(
      numericScore
    )
      ? numericScore
      : 0;

  let ringClass = "";

  if (safeScore >= 75) {
    ringClass =
      "from-emerald-400 via-green-500 to-teal-500";
  } else if (safeScore >= 50) {
    ringClass =
      "from-amber-300 via-orange-400 to-amber-500";
  } else {
    ringClass =
      "from-rose-400 via-red-500 to-pink-500";
  }

  return (
    <div className="relative flex h-64 w-64 items-center justify-center sm:h-72 sm:w-72">

      <div
        className={`absolute inset-0 rounded-full bg-gradient-to-br ${ringClass} opacity-20 blur-2xl`}
      />

      <div
        className={`relative flex h-full w-full items-center justify-center rounded-full bg-gradient-to-br ${ringClass} p-2 shadow-2xl`}
      >

        <div className="flex h-full w-full flex-col items-center justify-center rounded-full bg-white">

          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
            Feasibility
          </p>

          <div className="mt-2 flex items-baseline">

            <span className="text-5xl font-black tracking-tight text-slate-950 sm:text-6xl">

              {Number.isInteger(
                safeScore
              )
                ? safeScore
                : safeScore.toFixed(
                    2
                  )}

            </span>

            <span className="ml-1 text-xl font-bold text-slate-400">
              /100
            </span>

          </div>

          <div className="mt-3 rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">
            {getScoreLabel(
              safeScore
            )}
          </div>

        </div>

      </div>

    </div>
  );
}

/* =========================================================
   PURCHASING POWER STATUS
========================================================= */

function getPurchasingPowerStatus(
  result: AnalysisResult
): string {
  if (
    result.purchasing_power_level
  ) {
    return result.purchasing_power_level;
  }

  const score = Number(
    result.purchasing_power
  );

  if (!Number.isFinite(score)) {
    return "--";
  }

  if (score >= 70) {
    return "Good";
  }

  return "Moderate";
}

/* =========================================================
   WEATHER CONDITION
========================================================= */

function getWeatherCondition(
  weatherCode?: number
): string {
  if (
    weatherCode === undefined
  ) {
    return "Normal";
  }

  if (weatherCode === 0) {
    return "Normal";
  }

  if (
    weatherCode >= 1 &&
    weatherCode <= 3
  ) {
    return "Cloudy";
  }

  if (
    weatherCode >= 45 &&
    weatherCode <= 48
  ) {
    return "Foggy";
  }

  if (
    (weatherCode >= 51 &&
      weatherCode <= 67) ||
    (weatherCode >= 80 &&
      weatherCode <= 82)
  ) {
    return "Rainy";
  }

  if (
    (weatherCode >= 71 &&
      weatherCode <= 77) ||
    weatherCode === 85 ||
    weatherCode === 86
  ) {
    return "Snowy";
  }

  if (
    weatherCode >= 95 &&
    weatherCode <= 99
  ) {
    return "Stormy";
  }

  return "Normal";
}

/* =========================================================
   FEASIBILITY HELPERS
========================================================= */

function getFeasibilityScore(
  result: AnalysisResult
): number | string {
  if (
    result.feasibility &&
    typeof result.feasibility ===
      "object"
  ) {
    return (
      result.feasibility
        .feasibility_score ??
      result.feasibility.score ??
      "--"
    );
  }

  if (
    typeof result.feasibility ===
    "number"
  ) {
    return result.feasibility;
  }

  return "--";
}

/* =========================================================
   RECOMMENDATION
========================================================= */

function getRecommendation(
  result: AnalysisResult
): string {
  if (
    result.feasibility &&
    typeof result.feasibility ===
      "object"
  ) {
    return (
      result.feasibility
        .recommendation ??
      getScoreLabel(
        Number(
          result.feasibility
            .feasibility_score ??
            0
        )
      )
    );
  }

  if (
    typeof result.feasibility ===
    "number"
  ) {
    return getScoreLabel(
      result.feasibility
    );
  }

  return "--";
}

/* =========================================================
   SCORE LABEL
========================================================= */

function getScoreLabel(
  score: number
): string {
  if (score >= 80) {
    return "Excellent Opportunity";
  }

  if (score >= 65) {
    return "Good Opportunity";
  }

  if (score >= 50) {
    return "Moderate Opportunity";
  }

  if (score >= 35) {
    return "Needs Evaluation";
  }

  return "High Risk";
}

/* =========================================================
   CLAMP
========================================================= */

function clamp(
  value: number
): number {
  if (
    !Number.isFinite(value)
  ) {
    return 0;
  }

  return Math.min(
    Math.max(value, 0),
    100
  );
}