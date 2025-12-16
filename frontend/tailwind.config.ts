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
        // Forkast Brand Colors
        forkast: {
          // Primary green - used for CTAs, buttons, accents
          green: {
            50: '#E8F9EE',
            100: '#C5F0D5',
            200: '#9FE6BA',
            300: '#79DC9F',
            400: '#53D284',
            500: '#00C853', // Primary brand green
            600: '#00B34A',
            700: '#009E42',
            800: '#008939',
            900: '#006B2C',
          },
          // Dark colors for text and footer
          dark: {
            50: '#F5F5F5',
            100: '#E8E8E8',
            200: '#D1D1D1',
            300: '#B0B0B0',
            400: '#888888',
            500: '#6B6B6B',
            600: '#5A5A5A',
            700: '#3D3D3D',
            800: '#2A2A2A',
            900: '#1A1A1A', // Footer/dark sections
          },
        },
      },
    },
  },
  plugins: [],
};
export default config;
