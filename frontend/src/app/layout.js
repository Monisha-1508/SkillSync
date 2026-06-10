import { Space_Grotesk, Inter } from "next/font/google";
import { AuthProvider } from "@/lib/AuthContext";
import "@/styles/globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const body = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});

export const metadata = {
  title: "SkillSync AI - your placement plan, built and explained",
  description:
    "Tell it where you stand and where you want to land. SkillSync AI maps the gap, " +
    "builds a week-by-week plan around your hours, and shows its reasoning at every step.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body className="font-body bg-cap-cloud text-cap-ink antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
