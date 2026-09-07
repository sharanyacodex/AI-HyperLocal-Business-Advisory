"use client";

import { useState, FormEvent } from "react";
import type { BusinessInputValues } from "@/lib/types";

const sections = ["Business", "Financial", "Financing"];

const inputClass =
  "w-full rounded-xl border border-navy/15 bg-white px-4 py-2.5 text-navy placeholder:text-navy/30 focus:border-skyaccent focus:outline-none";
const labelClass = "text-sm font-medium text-navy/80";
const helpClass = "mt-1 text-xs text-navy/50";

export default function BusinessInputForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (values: BusinessInputValues) => void;
  submitting: boolean;
}) {
  const [values, setValues] = useState<BusinessInputValues>({
    requested_loan_amount: 500000,
    beneficiary_category: "general",
    location_type: "rural",
    business_sector: "manufacturing",
    tarun_plus_eligible: false,
    available_margin: 100000,
    monthly_revenue: 50000,
    monthly_operating_cost: 30000,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(values);
  }

  function num(v: string) {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-2xl px-6 py-14">
      <ol className="mb-10 flex items-center gap-6 text-sm text-navy/50">
        {sections.map((s, i) => (
          <li key={s} className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full border border-navy/20 text-xs">
              {i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>

      <h1 className="font-display text-3xl text-navy">Tell us about your business</h1>
      <p className="mt-2 text-navy/60">
        These figures feed the financial engine directly &mdash; nothing here
        is calculated by this form.
      </p>

      <div className="glass mt-10 rounded-2xl p-7">
        <h2 className="font-display text-xl italic text-navy">Business information</h2>
        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <label className={labelClass}>Beneficiary category *</label>
            <select
              className={inputClass + " mt-1.5"}
              value={values.beneficiary_category}
              onChange={(e) =>
                setValues({ ...values, beneficiary_category: e.target.value })
              }
            >
              <option value="general">General</option>
              <option value="special">Special (SC/ST/OBC/women/etc.)</option>
            </select>
            <p className={helpClass}>Used to match PMEGP eligibility rules.</p>
          </div>
          <div>
            <label className={labelClass}>Location *</label>
            <select
              className={inputClass + " mt-1.5"}
              value={values.location_type}
              onChange={(e) =>
                setValues({ ...values, location_type: e.target.value })
              }
            >
              <option value="rural">Rural</option>
              <option value="urban">Urban</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className={labelClass}>Business sector *</label>
            <select
              className={inputClass + " mt-1.5"}
              value={values.business_sector}
              onChange={(e) =>
                setValues({ ...values, business_sector: e.target.value })
              }
            >
              <option value="manufacturing">Manufacturing</option>
              <option value="business_service">Business / Service</option>
              <option value="retail">Retail / Other</option>
            </select>
            <p className={helpClass}>
              Manufacturing and business/service map to PMEGP project-cost
              ceilings; other sectors will only be checked against PMMY.
            </p>
          </div>
        </div>
      </div>

      <div className="glass mt-6 rounded-2xl p-7">
        <h2 className="font-display text-xl italic text-navy">Financial information</h2>
        <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div>
            <label className={labelClass}>Requested loan amount (₹) *</label>
            <input
              type="number"
              min={1}
              required
              className={inputClass + " mt-1.5"}
              value={values.requested_loan_amount}
              onChange={(e) =>
                setValues({
                  ...values,
                  requested_loan_amount: num(e.target.value),
                })
              }
            />
          </div>
          <div>
            <label className={labelClass}>Available margin / own capital (₹) *</label>
            <input
              type="number"
              min={1}
              required
              className={inputClass + " mt-1.5"}
              value={values.available_margin}
              onChange={(e) =>
                setValues({ ...values, available_margin: num(e.target.value) })
              }
            />
          </div>
          <div>
            <label className={labelClass}>Monthly revenue (₹) *</label>
            <input
              type="number"
              min={0}
              required
              className={inputClass + " mt-1.5"}
              value={values.monthly_revenue}
              onChange={(e) =>
                setValues({ ...values, monthly_revenue: num(e.target.value) })
              }
            />
          </div>
          <div>
            <label className={labelClass}>Monthly operating cost (₹) *</label>
            <input
              type="number"
              min={0}
              required
              className={inputClass + " mt-1.5"}
              value={values.monthly_operating_cost}
              onChange={(e) =>
                setValues({
                  ...values,
                  monthly_operating_cost: num(e.target.value),
                })
              }
            />
          </div>
        </div>
      </div>

      <div className="glass mt-6 rounded-2xl p-7">
        <h2 className="font-display text-xl italic text-navy">Financing information</h2>
        <label className="mt-5 flex items-start gap-3 text-sm text-navy/80">
          <input
            type="checkbox"
            className="mt-0.5 h-4 w-4"
            checked={values.tarun_plus_eligible}
            onChange={(e) =>
              setValues({ ...values, tarun_plus_eligible: e.target.checked })
            }
          />
          <span>
            I have already repaid a PMMY Tarun loan and am eligible for
            Tarun Plus.
          </span>
        </label>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="mt-10 w-full rounded-full bg-navy py-3.5 font-medium text-white transition hover:bg-navy-600 disabled:opacity-50"
      >
        {submitting ? "Analyzing…" : "Analyze my business"}
      </button>
    </form>
  );
}
