import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E2E8F0",
        navy: {
          DEFAULT: "#0A193F",
          deep: "#0F172A",
        },
        emerald: {
          DEFAULT: "#10B981",
          hover: "#0E9F71",
        },
        amber: {
          DEFAULT: "#F59E0B",
          hover: "#DB8B09",
        },
        accentBlue: "#3B82F6",
        accentOrange: "#F97316",
        accentTeal: "#14B8A6",
        accentPurple: "#8B5CF6",
      },
      fontFamily: {
        heading: ["var(--font-manrope)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "8px",
        sm: "6px",
        lg: "10px",
      },
      maxWidth: {
        content: "1120px",
      },
    },
  },
  plugins: [],
};

export default config;