import React from 'react';
import { Landmark, Settings, ShieldCheck, Sparkles } from 'lucide-react';

interface HeaderProps {
  apiBaseUrl: string;
  onOpenSettings: () => void;
  isBackendConnected?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  apiBaseUrl,
  onOpenSettings,
}) => {
  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-30 flex items-center justify-between px-4 sm:px-8">
      <div className="max-w-6xl w-full mx-auto flex items-center justify-between gap-4">
        {/* Brand & Module Identification */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white shadow-sm font-bold text-lg">
            <span>V</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 leading-none">
                Vyapar<span className="text-indigo-600">Disha</span>
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-bold bg-indigo-50 text-indigo-600 rounded uppercase tracking-wider">
                Module 2
              </span>
            </div>
            <p className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold mt-0.5">
              Financial and Scheme Planning
            </p>
          </div>
        </div>

        {/* Right Controls: Backend Endpoint & Settings */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenSettings}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-all shadow-xs cursor-pointer"
            title="Configure FastAPI Backend URL"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="hidden sm:inline text-slate-400">API:</span>
            <span className="font-mono text-[11px] text-indigo-600 font-semibold truncate max-w-[130px] sm:max-w-[180px]">
              {apiBaseUrl.replace(/^https?:\/\//, '')}
            </span>
            <Settings className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>
      </div>
    </header>
  );
};
