import type { Config } from "tailwindcss";

/**
 * Repurpose AI analytics dashboard design tokens.
 * Visual language: Linear dark-mode system (near-black canvas, translucent
 * surfaces, indigo-violet brand accent, Inter typeface).
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#08090a",
        panel: "#0f1011",
        surface: "#191a1b",
        surface2: "#28282c",
        ink: {
          DEFAULT: "#f7f8f8",
          soft: "#d0d6e0",
          muted: "#8a8f98",
          faint: "#62666d",
        },
        brand: {
          DEFAULT: "#5e6ad2",
          bright: "#7170ff",
          hover: "#828fff",
        },
        line: {
          DEFAULT: "rgba(255,255,255,0.08)",
          subtle: "rgba(255,255,255,0.05)",
        },
        success: "#27a644",
        emerald: "#10b981",
        warning: "#f5a524",
        danger: "#f2646a",
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
      borderRadius: {
        micro: "2px",
        sm2: "4px",
        DEFAULT: "6px",
        card: "8px",
        panel: "12px",
      },
      boxShadow: {
        card: "rgba(0,0,0,0.2) 0px 0px 0px 1px",
        dialog:
          "rgba(0,0,0,0) 0px 8px 2px, rgba(0,0,0,0.01) 0px 5px 2px, rgba(0,0,0,0.04) 0px 3px 2px, rgba(0,0,0,0.07) 0px 1px 1px, rgba(0,0,0,0.08) 0px 0px 1px",
        focus: "rgba(0,0,0,0.1) 0px 4px 12px",
      },
      letterSpacing: {
        display: "-0.03em",
        tight2: "-0.02em",
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-soft": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.45" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.35s ease-out both",
        "pulse-soft": "pulse-soft 1.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
