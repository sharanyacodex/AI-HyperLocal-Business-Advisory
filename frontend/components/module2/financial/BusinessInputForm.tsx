"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { FormField } from "@/components/module2/ui/FormField";
import { Select } from "@/components/module2/ui/Select";
import { Button } from "@/components/module2/ui/Button";
import {
  BUSINESS_CATEGORY_OPTIONS,
  BusinessCategory,
  BusinessInput,
} from "@/types/module2/financial";

type FormState = Record<keyof BusinessInput, string>;

const initialState: FormState = {
  location: "",
  businessCategory: "retail",
  ownCapital: "",
  expectedMonthlyRevenue: "",
  monthlyOperatingCosts: "",
  existingDebt: "0",
  existingAssetsValue: "0",
  experienceYears: "",
  numberOfWorkers: "1",
};

const numericFields: (keyof BusinessInput)[] = [
  "ownCapital",
  "expectedMonthlyRevenue",
  "monthlyOperatingCosts",
  "existingDebt",
  "existingAssetsValue",
  "experienceYears",
  "numberOfWorkers",
];

export function BusinessInputForm() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(initialState);
  const [errors, setErrors] = useState<Partial<Record<keyof BusinessInput, string>>>({});

  function updateField(field: keyof BusinessInput, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function validate(): boolean {
    const nextErrors: Partial<Record<keyof BusinessInput, string>> = {};

    if (!form.location.trim()) {
      nextErrors.location = "Enter a location.";
    }
    if (!form.ownCapital || Number(form.ownCapital) < 0) {
      nextErrors.ownCapital = "Enter the capital you can contribute.";
    }
    if (!form.expectedMonthlyRevenue || Number(form.expectedMonthlyRevenue) <= 0) {
      nextErrors.expectedMonthlyRevenue = "Enter expected monthly revenue.";
    }
    if (!form.monthlyOperatingCosts || Number(form.monthlyOperatingCosts) < 0) {
      nextErrors.monthlyOperatingCosts = "Enter monthly operating costs.";
    }
    if (form.experienceYears === "" || Number(form.experienceYears) < 0) {
      nextErrors.experienceYears = "Enter years of experience.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!validate()) {
      return;
    }

    const payload: BusinessInput = {
      location: form.location.trim(),
      businessCategory: form.businessCategory as BusinessCategory,
      ownCapital: Number(form.ownCapital),
      expectedMonthlyRevenue: Number(form.expectedMonthlyRevenue),
      monthlyOperatingCosts: Number(form.monthlyOperatingCosts),
      existingDebt: Number(form.existingDebt || 0),
      existingAssetsValue: Number(form.existingAssetsValue || 0),
      experienceYears: Number(form.experienceYears),
      numberOfWorkers: Number(form.numberOfWorkers || 1),
    };

    // Stored for the results screen to read until the service layer
    // (Phase 8) replaces this with a real API submission.
    sessionStorage.setItem("module2:businessInput", JSON.stringify(payload));
    router.push("/module2/results");
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-8">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <FormField
          id="location"
          label="Business location"
          placeholder="e.g. Bhatpara, West Bengal"
          value={form.location}
          onChange={(e) => updateField("location", e.target.value)}
          error={errors.location}
        />
        <Select
          id="businessCategory"
          label="Business category"
          options={BUSINESS_CATEGORY_OPTIONS}
          value={form.businessCategory}
          onChange={(e) => updateField("businessCategory", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <FormField
          id="ownCapital"
          label="Own capital / margin (₹)"
          type="number"
          min={0}
          placeholder="e.g. 50000"
          value={form.ownCapital}
          onChange={(e) => updateField("ownCapital", e.target.value)}
          error={errors.ownCapital}
        />
        <FormField
          id="expectedMonthlyRevenue"
          label="Expected monthly revenue (₹)"
          type="number"
          min={0}
          placeholder="e.g. 80000"
          value={form.expectedMonthlyRevenue}
          onChange={(e) => updateField("expectedMonthlyRevenue", e.target.value)}
          error={errors.expectedMonthlyRevenue}
        />
        <FormField
          id="monthlyOperatingCosts"
          label="Monthly operating costs (₹)"
          type="number"
          min={0}
          placeholder="e.g. 45000"
          value={form.monthlyOperatingCosts}
          onChange={(e) => updateField("monthlyOperatingCosts", e.target.value)}
          error={errors.monthlyOperatingCosts}
        />
        <FormField
          id="existingDebt"
          label="Existing debt (₹)"
          hint="Enter 0 if none."
          type="number"
          min={0}
          value={form.existingDebt}
          onChange={(e) => updateField("existingDebt", e.target.value)}
        />
        <FormField
          id="existingAssetsValue"
          label="Existing assets value (₹)"
          hint="Enter 0 if none."
          type="number"
          min={0}
          value={form.existingAssetsValue}
          onChange={(e) => updateField("existingAssetsValue", e.target.value)}
        />
        <FormField
          id="experienceYears"
          label="Years of experience"
          type="number"
          min={0}
          placeholder="e.g. 3"
          value={form.experienceYears}
          onChange={(e) => updateField("experienceYears", e.target.value)}
          error={errors.experienceYears}
        />
        <FormField
          id="numberOfWorkers"
          label="Number of workers"
          hint="Include yourself if you work in the business."
          type="number"
          min={1}
          value={form.numberOfWorkers}
          onChange={(e) => updateField("numberOfWorkers", e.target.value)}
        />
      </div>

      <div>
        <Button type="submit" variant="primary">
          Calculate feasibility
        </Button>
      </div>
    </form>
  );
}