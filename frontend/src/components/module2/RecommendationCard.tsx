import React from 'react';
import { ResponseSection } from '../../types/module2';
import { DynamicFieldGrid } from './DynamicFieldGrid';
import { ArrowRight, Sparkles } from 'lucide-react';

interface RecommendationCardProps {
  data: ResponseSection | string;
  onRecalculate?: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ data, onRecalculate }) => {
  const isString = typeof data === 'string';

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 sm:p-6 flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Recommendation
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              recommendation — as returned by the backend
            </p>
          </div>
        </div>
        <span className="text-[10px] px-2.5 py-0.5 bg-indigo-50 text-indigo-600 rounded font-bold uppercase tracking-wider">
          Backend Computed
        </span>
      </div>

      {isString ? (
        <p className="text-sm text-slate-700 leading-relaxed">{data as string}</p>
      ) : (
        <DynamicFieldGrid data={data as Record<string, unknown>} />
      )}

      {onRecalculate && (
        <div className="mt-5 pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={onRecalculate}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 cursor-pointer"
          >
            <span>Adjust inputs and recalculate</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
};
