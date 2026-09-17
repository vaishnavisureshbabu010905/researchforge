import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1115",
        panel: "#161922",
        border: "#262b38",
        accent: "#5b8cff",
        good: "#3fb97f",
        warn: "#e0a83e",
        bad: "#e05a5a",
      },
    },
  },
  plugins: [],
};

export default config;
