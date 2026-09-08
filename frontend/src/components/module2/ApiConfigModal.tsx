import React, { useState } from 'react';
import { X, Server, CheckCircle2, AlertCircle, RefreshCw, Globe, HelpCircle } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl, resetApiBaseUrl } from '../../lib/api';

interface ApiConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUrlUpdated: (newUrl: string) => void;
}

export const ApiConfigModal: React.FC<ApiConfigModalProps> = ({
  isOpen,
  onClose,
  onUrlUpdated,
}) => {
  const currentUrl = getApiBaseUrl();
  const [urlInput, setUrlInput] = useState(currentUrl);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    const testUrl = urlInput.trim().replace(/\/$/, '');
    try {
      // Test either health or options/docs endpoint
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);

      const res = await fetch(`${testUrl}/docs`, {
        method: 'GET',
        signal: controller.signal,
        mode: 'no-cors', // standard test if server is alive
      });
      clearTimeout(timeoutId);

      setTestResult({
        success: true,
        message: `Connection reachable to server at ${testUrl}`,
      });
    } catch (err: any) {
      setTestResult({
        success: false,
        message: `Could not reach ${testUrl}. Check that your FastAPI server is running with CORS enabled (e.g. uvicorn main:app --reload --port 8000).`,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const sanitized = urlInput.trim().replace(/\/$/, '');
    setApiBaseUrl(sanitized);
    onUrlUpdated(sanitized);
    onClose();
  };

  const handleReset = () => {
    resetApiBaseUrl();
    const def = getApiBaseUrl();
    setUrlInput(def);
    onUrlUpdated(def);
    setTestResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 shadow-xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              FastAPI Backend Configuration
            </h3>
            <p className="text-xs text-slate-500">
              Configure connection to your Python FastAPI backend
            </p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Backend Base URL (NEXT_PUBLIC_API_BASE_URL)
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                <Globe className="w-4 h-4" />
              </span>
              <input
                type="text"
                value={urlInput}
                onChange={(e) => {
                  setUrlInput(e.target.value);
                  setTestResult(null);
                }}
                placeholder="http://127.0.0.1:8000"
                className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              Default is <code className="text-indigo-600 bg-slate-100 px-1 py-0.5 rounded">http://127.0.0.1:8000</code>. Saved in browser storage for active session.
            </p>
          </div>

          {/* Test connection result */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-start gap-2 ${
                testResult.success
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}
            >
              {testResult.success ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              )}
              <span className="leading-relaxed">{testResult.message}</span>
            </div>
          )}

          {/* Primary Endpoint reference */}
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1.5">
            <div className="text-slate-500 font-medium">Configured Primary Endpoint:</div>
            <div className="font-mono text-indigo-600 text-[11px] break-all">
              POST {urlInput}/api/module2/integration/calculate
            </div>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-slate-100 gap-2">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={isTesting}
                className="px-3 py-2 text-xs font-bold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors inline-flex items-center gap-1.5 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
                <span>Test Ping</span>
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-2 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
              >
                Reset Default
              </button>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-2 text-xs text-slate-500 hover:text-slate-800 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs transition-colors cursor-pointer"
              >
                Save URL
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
