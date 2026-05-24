import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#161616",
        paper: "#f7f4ef",
        signal: "#147a64",
        deal: "#d9480f"
      }
    }
  },
  plugins: []
};

export default config;
