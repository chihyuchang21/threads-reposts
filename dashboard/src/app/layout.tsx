import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Threads Ideas",
  description: "Weekly review of your reposted ideas",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>
        <nav
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "16px 32px",
            borderBottom: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          <span style={{ fontWeight: 700, fontSize: 16, color: "var(--accent)" }}>
            ✦ Threads Ideas
          </span>
          <span style={{ flex: 1 }} />
          <Link href="/" style={navLink}>Overview</Link>
          <Link href="/review" style={navLink}>Review</Link>
          <Link href="/library" style={navLink}>Library</Link>
        </nav>
        <main style={{ minHeight: "calc(100vh - 57px)" }}>{children}</main>
      </body>
    </html>
  );
}

const navLink: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: 8,
  color: "var(--text-dim)",
  textDecoration: "none",
  fontSize: 14,
  fontWeight: 500,
  transition: "color 0.15s",
};
