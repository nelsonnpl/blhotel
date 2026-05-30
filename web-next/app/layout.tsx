import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Revenue Intelligence",
  description: "Panel revenue con MapLibre + ECharts",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
