import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cogniflow",
  description: "AI-powered document analysis and knowledge management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
