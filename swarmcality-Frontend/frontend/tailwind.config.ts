import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        base: "#0A0A0F",
        elevated: "#13131A",
        card: "#1A1A24",
        border: "#252535",
        "border-light": "#2E2E42",
        accent: "#7C5CF6",
        "accent-hover": "#8F72F8",
        "accent-dim": "#7C5CF620",
        primary: "#E8E8F0",
        secondary: "#8888A8",
        success: "#22C55E",
        danger: "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
        spin: "spin 1s linear infinite",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};

export default config;
