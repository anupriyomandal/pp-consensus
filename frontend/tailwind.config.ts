import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        shell: "#0f172a",
        canvas: "#f8fafc",
        accent: "#0ea5e9",
      },
      fontFamily: {
        sans: ["Avenir Next", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        card: "0 20px 40px -24px rgba(15, 23, 42, 0.35)",
      },
      backgroundImage: {
        grid:
          "linear-gradient(to right, rgba(15,23,42,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(15,23,42,0.05) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "40px 40px",
      },
    },
  },
  plugins: [],
};

export default config;
