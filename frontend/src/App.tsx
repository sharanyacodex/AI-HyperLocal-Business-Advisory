import React, { useState, useRef } from 'react';
import { Header } from './components/module2/Header';
import { FinancialInputForm } from './components/module2/FinancialInputForm';
import { FinancialSummary } from './components/module2/FinancialSummary';
import { RepaymentAssessment } from './components/module2/RepaymentAssessment';
import { SchemeCard } from './components/module2/SchemeCard';
import { SubsidyInfo } from './components/module2/SubsidyInfo';
import { RecommendationCard } from './components/module2/RecommendationCard';
import { ApiConfigModal } from './components/module2/ApiConfigModal';
import { FinancialPlanRequest, Module2CalculateResponse } from './types/module2';
import { calculateFinancialPlan, getApiBaseUrl, KNOWN_GOOD_SAMPLE_REQUEST } from './lib/api';
import { AlertCircle, RefreshCw, Sparkles, CheckCircle2, Sliders } from 'lucide-react';

export default function App() {
  const [apiBaseUrl, setApiBaseUrlState] = useState<string>(getApiBaseUrl());
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);

  const [formData, setFormData] = useState<FinancialPlanRequest>(KNOWN_GOOD_SAMPLE_REQUEST);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Module2CalculateResponse | null>(null);
  const [dataSourceNotice, setDataSourceNotice] = useState<string | null>(null);

  const resultsRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLDivElement>(null);

  const handleFormSubmit = async (values: FinancialPlanRequest) => {
    setIsLoading(true);
    setError(null);
    setDataSourceNotice(null);
    setFormData(values);

    try {
      const response = await calculateFinancialPlan(values);
      setResult(response);
      setDataSourceNotice(`Calculated via FastAPI backend (${getApiBaseUrl()})`);

      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err: any) {
      console.error('Calculation error:', err);
      setError(err.message || 'An unexpected error occurred while communicating with the backend.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseSampleData = () => {
    setFormData(KNOWN_GOOD_SAMPLE_REQUEST);
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleRecalculate = () => {
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Header apiBaseUrl={apiBaseUrl} onOpenSettings={() => setIsConfigOpen(true)} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
        <div className="mb-8 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-slate-200 text-xs font-semibold text-slate-600 shadow-xs mb-3">
            <Sliders className="w-3.5 h-3.5 text-indigo-600" />
            <span>VyaparDisha Core Module 2</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Financial and Scheme Planning
          </h1>
          <p className="mt-2 text-sm sm:text-base text-slate-500 max-w-3xl leading-relaxed">
            Connects directly to the existing VyaparDisha FastAPI calculation engine to assess MSME scheme
            eligibility, compute project financing structure, and evaluate repayment stress. All calculations
            are performed by the backend — this UI only collects inputs and displays results.
          </p>
        </div>

        <div ref={formRef} className="mb-10">
          <FinancialInputForm
            initialValues={formData}
            onSubmit={handleFormSubmit}
            isLoading={isLoading}
            onUseSampleData={handleUseSampleData}
          />
        </div>

        {error && (
          <div className="mb-8 p-4 sm:p-5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 shadow-sm">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-bold text-rose-900 mb-1">
                  Calculation Request Unsuccessful
                </h4>
                <p className="text-xs sm:text-sm text-rose-700 leading-relaxed font-sans">{error}</p>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => handleFormSubmit(formData)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors cursor-pointer shadow-xs"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Retry Request</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleUseSampleData}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors cursor-pointer shadow-xs"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    <span>Load Known-Good Sample</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsConfigOpen(true)}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold underline underline-offset-4 cursor-pointer"
                  >
                    Change Backend URL ({apiBaseUrl})
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div ref={resultsRef} className="space-y-6 pt-4 border-t border-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-white border border-slate-200 rounded-xl shadow-xs text-xs">
              <div className="flex items-center gap-2 text-emerald-700 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Financial Plan Successfully Evaluated</span>
              </div>
              {dataSourceNotice && (
                <span className="text-slate-500 font-mono text-[11px]">{dataSourceNotice}</span>
              )}
            </div>

            <FinancialSummary data={result.financial_summary} />
            <RepaymentAssessment data={result.repayment} />
            <SchemeCard data={result.scheme_match} />
            <SubsidyInfo data={result.subsidy_information} />

            {result.recommendation !== undefined && result.recommendation !== null && (
              <RecommendationCard data={result.recommendation} onRecalculate={handleRecalculate} />
            )}
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto px-4">
          <p>
            <span className="font-semibold text-slate-700">VyaparDisha</span> • Module 2: Financial and Scheme Planning
          </p>
          <p className="mt-1 text-[11px] text-slate-400">
            Designed for institutional MSME decision support. Source of truth: FastAPI Backend Calculation Engine.
          </p>
        </div>
      </footer>

      <ApiConfigModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        onUrlUpdated={(url) => setApiBaseUrlState(url)}
      />
    </div>
  );
}
