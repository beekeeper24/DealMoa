import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DealMoa",
  description: "Search-first hot deal and auction discovery"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
