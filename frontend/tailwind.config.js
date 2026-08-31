export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F5F7F4",
        card: "#FFFFFF",
        primary: { DEFAULT: "#5C7A29", hover: "#48621F" },
        accent: "#D6A62C",
        ink: { DEFAULT: "#172019", soft: "#66736A" },
        border: "#DDE3DD",
        risk: { legit: "#2E8B57", suspicious: "#D99000", high: "#D64545", extreme: "#8B0000" }
      },
      boxShadow: {
        card: "0 1px 2px rgba(23,32,25,.04), 0 4px 16px rgba(23,32,25,.06)",
        lift: "0 6px 24px rgba(23,32,25,.10)"
      }
    }
  },
  plugins: []
};
