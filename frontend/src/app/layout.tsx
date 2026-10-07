import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Scam Shield",
  description: "Real-time scam co-pilot",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
