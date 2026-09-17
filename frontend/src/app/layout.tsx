import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResearchForge",
  description: "Multi-Agent Deep Research, Built for Evidence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-ink text-white antialiased">
        <header className="border-b border-border">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="flex items-baseline gap-2">
              <span className="text-lg font-semibold tracking-tight">ResearchForge</span>
              <span className="text-xs text-white/40">Multi-Agent Deep Research, Built for Evidence.</span>
            </Link>
            <nav className="flex gap-5 text-sm text-white/70">
              <Link href="/" className="hover:text-white">Dashboard</Link>
              <Link href="/history" className="hover:text-white">History</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
