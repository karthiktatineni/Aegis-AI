import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis AI",
  description: "Local-first AI platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
