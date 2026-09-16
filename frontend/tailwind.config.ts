import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16212b",
        canvas: "#f5f7f5",
        mint: "#d8f3e4",
        signal: "#e1724f",
      },
    },
  },
  plugins: [],
};

export default config;
