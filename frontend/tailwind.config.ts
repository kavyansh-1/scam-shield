import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#10262E", paper: "#F1F5F6", line: "#CBD6DA", brand: "#0E6B7A",
        safe: "#14632E", warn: "#8A5300", danger: "#B3171C",
      },
    },
  },
  plugins: [],
};
export default config;
