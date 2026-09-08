import React, { useState } from 'react';
import { FinancialPlanRequest, ManualOverrides } from '../../types/module2';
import { Building2, IndianRupee, ArrowRight, Loader2, Sparkles, AlertCircle, SlidersHorizontal, ChevronDown } from 'lucide-react';
import { formatINR } from '../../lib/formatters';

interface FinancialInputFormProps {
  initialValues: FinancialPlanRequest;
  onSubmit: (values: FinancialPlanRequest) => void;
  isLoading: boolean;
  onUseSampleData?: () => void;
}

const DEFAULT_OVERRIDES: ManualOverrides = {
  contribution_rate: 0.1,
  project_cost_limit: 5000000,
  loan_limit: 4500000,
  interest_rate: 8,
  tenure_months: 84,
};

export const FinancialInputForm: React.FC<FinancialInputFormProps> = ({
  initialValues,
  onSubmit,
  isLoading,
  onUseSampleData,
}) => {
  const [formData, setFormData] = useState<FinancialPlanRequest>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showOverrides, setShowOverrides] = useState<boolean>(!!initialValues.manual_overrides);

  const handleChange = (field: keyof FinancialPlanRequest, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field as string];
        return next;
      });
    }
  };

  const handleNumberChange = (field: keyof FinancialPlanRequest, rawVal: string) => {
    const clean = rawVal.replace(/[^0-9]/g, '');
    const num = clean === '' ? 0 : parseInt(clean, 10);
    handleChange(field, num);
  };

  const handleOverrideChange = (field: keyof ManualOverrides, value: number) => {
    setFormData((prev) => ({
      ...prev,
      manual_overrides: {
        ...(prev.manual_overrides || DEFAULT_OVERRIDES),
        [field]: value,
      },
    }));
  };

  const toggleOverrides = () => {
    setShowOverrides((prev) => {
      const next = !prev;
      setFormData((fd) => ({
        ...fd,
        manual_overrides: next ? (fd.manual_overrides || DEFAULT_OVERRIDES) : undefined,
      }));
      return next;
    });
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.beneficiary_category) newErrors.beneficiary_category = 'Required';
    if (!formData.location_type) newErrors.location_type = 'Required';
    if (!formData.business_sector) newErrors.business_sector = 'Required';
    if (!formData.selected_scheme_code) newErrors.selected_scheme_code = 'Required';
    if (!formData.available_margin || formData.available_margin <= 0) {
      newErrors.available_margin = 'Must be greater than ₹0';
    }
    if (!formData.requested_loan_amount || formData.requested_loan_amount <= 0) {
      newErrors.requested_loan_amount = 'Must be greater than ₹0';
    }
    if (!formData.monthly_revenue || formData.monthly_revenue <= 0) {
      newErrors.monthly_revenue = 'Must be greater than ₹0';
    }
    if (formData.monthly_operating_cost === undefined || formData.monthly_operating_cost < 0) {
      newErrors.monthly_operating_cost = 'Cannot be negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  const inputCls = (hasError: boolean) =>
    `w-full h-10 bg-white border ${
      hasError ? 'border-rose-400 ring-1 ring-rose-400' : 'border-slate-200'
    } rounded-lg pl-6 pr-3 text-sm font-medium text-slate-800 outline-none focus:ring-1 focus:ring-indigo-500 font-mono transition-colors`;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GROUP 1: BUSINESS / ELIGIBILITY */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3 mb-5">
              <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                <Building2 className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Business / Eligibility
                </h2>
                <p className="text-xs text-slate-500 font-medium">Enterprise classification & scheme alignment</p>
              </div>
            </div>

            <div className="space-y-4">
              {/* Beneficiary Category */}
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">
                  Beneficiary Category <span className="text-rose-500">*</span>
                </label>
                <select
                  value={formData.beneficiary_category}
                  onChange={(e) => handleChange('beneficiary_category', e.target.value)}
                  className={`w-full h-10 bg-slate-50 border ${
                    errors.beneficiary_category ? 'border-rose-400 ring-1 ring-rose-400' : 'border-slate-200'
                  } rounded-lg px-3 text-sm text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500 transition-colors`}
                >
                  <option value="general">General</option>
                  <option value="sc">SC</option>
                  <option value="st">ST</option>
                  <option value="obc">OBC</option>
                  <option value="women">Women</option>
                  <option value="minority">Minority</option>
                </select>
                {errors.beneficiary_category && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.beneficiary_category}
                  </p>
                )}
              </div>

              {/* Location Type */}
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">
                  Location Type <span className="text-rose-500">*</span>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {['rural', 'urban'].map((loc) => (
                    <button
                      key={loc}
                      type="button"
                      onClick={() => handleChange('location_type', loc)}
                      className={`h-10 px-3 text-xs font-semibold rounded-lg border transition-all text-center capitalize cursor-pointer ${
                        formData.location_type === loc
                          ? 'bg-indigo-50 border-indigo-500 text-indigo-700 shadow-xs'
                          : 'bg-slate-50 border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }`}
                    >
                      {loc}
                    </button>
                  ))}
                </div>
                {errors.location_type && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.location_type}
                  </p>
                )}
              </div>

              {/* Business Sector */}
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">
                  Business Sector <span className="text-rose-500">*</span>
                </label>
                <select
                  value={formData.business_sector}
                  onChange={(e) => handleChange('business_sector', e.target.value)}
                  className={`w-full h-10 bg-slate-50 border ${
                    errors.business_sector ? 'border-rose-400 ring-1 ring-rose-400' : 'border-slate-200'
                  } rounded-lg px-3 text-sm text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500 transition-colors`}
                >
                  <option value="manufacturing">Manufacturing</option>
                  <option value="service">Service</option>
                  <option value="trading">Trading / Retail</option>
                  <option value="agro">Agro-allied</option>
                </select>
                {errors.business_sector && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.business_sector}
                  </p>
                )}
              </div>

              {/* Selected Scheme Code */}
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">
                  Selected Scheme Code <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.selected_scheme_code}
                  onChange={(e) => handleChange('selected_scheme_code', e.target.value.toUpperCase())}
                  placeholder="e.g. PMEGP"
                  className={`w-full h-10 bg-slate-50 border ${
                    errors.selected_scheme_code ? 'border-rose-400 ring-1 ring-rose-400' : 'border-slate-200'
                  } rounded-lg px-3 text-sm text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500 font-mono transition-colors`}
                />
                {errors.selected_scheme_code && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.selected_scheme_code}
                  </p>
                )}
                <p className="text-[11px] text-slate-400 mt-1">
                  Exact scheme code as recognized by the backend (e.g. PMEGP, CGTMSE, PMMY).
                </p>
              </div>

              {/* Tarun Plus Eligible */}
              <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-3 h-10">
                <span className="text-xs font-semibold text-slate-600">Tarun Plus Eligible</span>
                <button
                  type="button"
                  onClick={() => handleChange('tarun_plus_eligible', !formData.tarun_plus_eligible)}
                  className={`relative w-9 h-5 rounded-full transition-colors cursor-pointer ${
                    formData.tarun_plus_eligible ? 'bg-indigo-600' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                      formData.tarun_plus_eligible ? 'translate-x-4' : ''
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* GROUP 2: FINANCIAL INPUTS */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 border-b border-slate-100 pb-3 mb-5">
              <div className="w-7 h-7 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                <IndianRupee className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Financial Inputs
                </h2>
                <p className="text-xs text-slate-500 font-medium">Margin, loan and cash-flow figures</p>
              </div>
            </div>

            <div className="space-y-4">
              {/* Available Margin */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase">
                    Available Margin <span className="text-rose-500">*</span>
                  </label>
                  <span className="text-[11px] font-mono text-indigo-600 font-bold">
                    {formatINR(formData.available_margin)}
                  </span>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-slate-400 text-xs font-bold">₹</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.available_margin || ''}
                    onChange={(e) => handleNumberChange('available_margin', e.target.value)}
                    placeholder="Available Margin"
                    className={inputCls(!!errors.available_margin)}
                  />
                </div>
                {errors.available_margin && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.available_margin}
                  </p>
                )}
              </div>

              {/* Requested Loan Amount */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase">
                    Requested Loan Amount <span className="text-rose-500">*</span>
                  </label>
                  <span className="text-[11px] font-mono text-indigo-600 font-bold">
                    {formatINR(formData.requested_loan_amount)}
                  </span>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-slate-400 text-xs font-bold">₹</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.requested_loan_amount || ''}
                    onChange={(e) => handleNumberChange('requested_loan_amount', e.target.value)}
                    placeholder="Requested Loan Amount"
                    className={inputCls(!!errors.requested_loan_amount)}
                  />
                </div>
                {errors.requested_loan_amount && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.requested_loan_amount}
                  </p>
                )}
              </div>

              {/* Monthly Revenue */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase">
                    Monthly Revenue <span className="text-rose-500">*</span>
                  </label>
                  <span className="text-[11px] font-mono text-slate-500">
                    {formatINR(formData.monthly_revenue)}
                  </span>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-slate-400 text-xs font-bold">₹</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.monthly_revenue || ''}
                    onChange={(e) => handleNumberChange('monthly_revenue', e.target.value)}
                    placeholder="Monthly Revenue"
                    className={inputCls(!!errors.monthly_revenue)}
                  />
                </div>
                {errors.monthly_revenue && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.monthly_revenue}
                  </p>
                )}
              </div>

              {/* Monthly Operating Cost */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[11px] font-bold text-slate-500 uppercase">
                    Monthly Operating Cost <span className="text-rose-500">*</span>
                  </label>
                  <span className="text-[11px] font-mono text-slate-500">
                    {formatINR(formData.monthly_operating_cost)}
                  </span>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-slate-400 text-xs font-bold">₹</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={formData.monthly_operating_cost || ''}
                    onChange={(e) => handleNumberChange('monthly_operating_cost', e.target.value)}
                    placeholder="Monthly Operating Cost"
                    className={inputCls(!!errors.monthly_operating_cost)}
                  />
                </div>
                {errors.monthly_operating_cost && (
                  <p className="mt-1 text-xs text-rose-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.monthly_operating_cost}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-slate-100 text-[11px] text-slate-400">
            All EMI, DSCR & scheme financial calculations are executed on the FastAPI backend. The frontend never computes these.
          </div>
        </div>
      </div>

      {/* GROUP 3: MANUAL OVERRIDES (optional) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6">
        <button
          type="button"
          onClick={toggleOverrides}
          className="w-full flex items-center justify-between cursor-pointer"
        >
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <SlidersHorizontal className="w-4 h-4" />
            </div>
            <div className="text-left">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Manual Overrides
              </h2>
              <p className="text-xs text-slate-500 font-medium">Optional — overrides scheme defaults if provided</p>
            </div>
          </div>
          <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${showOverrides ? 'rotate-180' : ''}`} />
        </button>

        {showOverrides && (
          <div className="mt-5 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Contribution Rate</label>
              <input
                type="number"
                step="0.01"
                value={formData.manual_overrides?.contribution_rate ?? DEFAULT_OVERRIDES.contribution_rate}
                onChange={(e) => handleOverrideChange('contribution_rate', Number(e.target.value))}
                className="w-full h-10 bg-slate-50 border border-slate-200 rounded-lg px-3 text-sm font-mono text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Project Cost Limit</label>
              <input
                type="number"
                value={formData.manual_overrides?.project_cost_limit ?? DEFAULT_OVERRIDES.project_cost_limit}
                onChange={(e) => handleOverrideChange('project_cost_limit', Number(e.target.value))}
                className="w-full h-10 bg-slate-50 border border-slate-200 rounded-lg px-3 text-sm font-mono text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Loan Limit</label>
              <input
                type="number"
                value={formData.manual_overrides?.loan_limit ?? DEFAULT_OVERRIDES.loan_limit}
                onChange={(e) => handleOverrideChange('loan_limit', Number(e.target.value))}
                className="w-full h-10 bg-slate-50 border border-slate-200 rounded-lg px-3 text-sm font-mono text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Interest Rate</label>
              <input
                type="number"
                step="0.1"
                value={formData.manual_overrides?.interest_rate ?? DEFAULT_OVERRIDES.interest_rate}
                onChange={(e) => handleOverrideChange('interest_rate', Number(e.target.value))}
                className="w-full h-10 bg-slate-50 border border-slate-200 rounded-lg px-3 text-sm font-mono text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1.5">Tenure (Months)</label>
              <input
                type="number"
                value={formData.manual_overrides?.tenure_months ?? DEFAULT_OVERRIDES.tenure_months}
                onChange={(e) => handleOverrideChange('tenure_months', Number(e.target.value))}
                className="w-full h-10 bg-slate-50 border border-slate-200 rounded-lg px-3 text-sm font-mono text-slate-700 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* ANALYZE BUTTON */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <div className="text-xs text-slate-500 text-center sm:text-left">
          Target Endpoint: <code className="text-indigo-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-mono text-[11px]">POST /api/module2/integration/calculate</code>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {onUseSampleData && (
            <button
              type="button"
              onClick={onUseSampleData}
              disabled={isLoading}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 h-11 px-4 text-xs font-bold text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl transition-all disabled:opacity-50 cursor-pointer shadow-xs"
              title="Fill the form with the confirmed working sample payload"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Load Known-Good Sample</span>
            </button>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 h-11 px-6 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] rounded-xl shadow-lg shadow-indigo-200 transition-all disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Calculating Plan...</span>
              </>
            ) : (
              <>
                <span>Calculate Financial Plan</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
};
