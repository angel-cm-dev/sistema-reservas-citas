/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef9f7", 100: "#d5f0eb", 200: "#ade1d8", 300: "#7ccbbf", 400: "#4fb0a3",
          500: "#349588", 600: "#28776e", 700: "#235f59", 800: "#1f4d49", 900: "#1c403d",
        },
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
