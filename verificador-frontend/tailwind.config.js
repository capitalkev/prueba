/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        "primary-focus": "#4f46e5",
        "primary-content": "#ffffff",
        "base-100": "#ffffff",
        "base-content": "#1f2937",
        "border-color": "#e5e7eb",
        neutral: "#f3f4f6",
        muted: "#6b7280",
        error: "#ef4444",
        secondary: "#0ea5e9"
      }
    }
  },
  plugins: []
};