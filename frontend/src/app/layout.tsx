import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: "Scam Shield - scam & UPI fraud co-pilot",
  description: "Spots digital-arrest and UPI scams in Hindi, English and Hinglish, and alerts your family.",
  manifest: "/manifest.json",
};
export const viewport: Viewport = { themeColor: "#0E6B7A", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
