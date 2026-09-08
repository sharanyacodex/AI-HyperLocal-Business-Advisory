import React from 'react';
import { ResponseSection } from '../../types/module2';
import { DynamicFieldGrid } from './DynamicFieldGrid';
import { Wallet } from 'lucide-react';

interface FinancialSummaryProps {
  data: ResponseSection;
}

export const FinancialSummary: React.FC<FinancialSummaryProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Wallet className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Financial Summary
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              financial_summary — as returned by the backend
            </p>
          </div>
        </div>
        <span className="text-[10px] px-2.5 py-0.5 bg-indigo-50 text-indigo-600 rounded font-bold uppercase tracking-wider">
          Backend Computed
        </span>
      </div>

      <DynamicFieldGrid data={data} />
    </div>
  );
};
