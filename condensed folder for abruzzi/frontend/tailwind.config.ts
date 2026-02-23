import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Kerne Color Palette
        green: "#37d097",
        teal: "#19b097",
        "lightest-grey": "#d4dce1",
        "light-grey": "#aab9be",
        grey: "#444a4f",
        "dark-grey": "#22252a",
      },
      fontFamily: {
        heading: ['TASA Orbiter', 'sans-serif'],
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      borderRadius: {
        sm: "4px",
      },
    },
  },
  plugins: [],
};

export default config;