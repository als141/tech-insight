import type { Metadata } from "next";

import { Providers } from "../components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "TechInsight",
  description: "Technical article knowledge management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
