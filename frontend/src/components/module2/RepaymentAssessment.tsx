import React from 'react';
import { ResponseSection } from '../../types/module2';
import { DynamicFieldGrid } from './DynamicFieldGrid';
import { Activity } from 'lucide-react';

interface RepaymentAssessmentProps {
  data: ResponseSection;
}

export const RepaymentAssessment: React.FC<RepaymentAssessmentProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Repayment Assessment
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              repayment — as returned by the backend
            </p>
          </div>
        </div>
        <span className="text-[10px] px-2.5 py-0.5 bg-amber-50 text-amber-600 rounded font-bold uppercase tracking-wider">
          Backend Computed
        </span>
      </div>

      <DynamicFieldGrid data={data} />
    </div>
  );
};
