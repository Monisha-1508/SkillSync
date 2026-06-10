/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,jsx}",
    "./src/components/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Capgemini brand palette - the deep "Capgemini Blue" is the primary
        // mark color, the lighter "vibrant blue" is the accent used on calls
        // to action and active states across capgemini.com.
        cap: {
          blue: "#0070AD",
          vibrant: "#17ABDA",
          navy: "#001E3C",
          ink: "#0B1F33",
          mist: "#EAF4FA",
          cloud: "#F5F9FC",
          slate: "#5B7184",
          line: "#D7E4ED",
        },
        signal: {
          good: "#1F9D55",
          warn: "#C77A1F",
          bad: "#C7401F",
          known: "#1F9D55",
          inferred: "#17ABDA",
          weak: "#C77A1F",
          unknown: "#8895A7",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        bento: "0 1px 2px rgba(11, 31, 51, 0.06), 0 8px 24px -12px rgba(0, 112, 173, 0.25)",
        "bento-hover": "0 2px 6px rgba(11, 31, 51, 0.08), 0 16px 40px -16px rgba(0, 112, 173, 0.35)",
      },
      borderRadius: {
        bento: "1.25rem",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(23, 171, 218, 0.45)" },
          "70%": { boxShadow: "0 0 0 12px rgba(23, 171, 218, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(23, 171, 218, 0)" },
        },
        countUp: {
          "0%": { opacity: "0.2" },
          "100%": { opacity: "1" },
        },
      },
      animation: {
        rise: "rise 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
        pulseRing: "pulseRing 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        countUp: "countUp 0.6s ease-out both",
      },
    },
  },
  plugins: [],
};
