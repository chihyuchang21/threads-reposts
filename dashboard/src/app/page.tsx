export const dynamic = "force-dynamic";

import Link from "next/link";
import { createClient } from "@supabase/supabase-js";

function serverClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

async function getStats() {
  const db = serverClient();
  const [pending, approved, cats] = await Promise.all([
    db.from("ideas").select("id", { count: "exact" }).eq("status", "pending"),
    db.from("ideas").select("id", { count: "exact" }).eq("status", "approved"),
    db
      .from("ideas")
      .select("category")
      .eq("status", "approved")
      .not("category", "is", null),
  ]);

  const categoryCount = new Set(cats.data?.map((r) => r.category)).size;
  return {
    pending: pending.count ?? 0,
    approved: approved.count ?? 0,
    categories: categoryCount,
  };
}

export default async function OverviewPage() {
  const stats = await getStats();

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "48px 32px" }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Overview</h1>
      <p style={{ color: "var(--text-dim)", marginBottom: 40, fontSize: 15 }}>
        你的 Threads 轉發想法庫
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 48 }}>
        <StatCard label="Pending Review" value={stats.pending} accent="var(--accent-2)" />
        <StatCard label="Ideas Saved" value={stats.approved} accent="var(--approved)" />
        <StatCard label="Categories" value={stats.categories} accent="var(--accent)" />
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        <Link href="/review">
          <button className="btn btn-keep" style={{ padding: "12px 28px", fontSize: 15 }}>
            開始 Review →
          </button>
        </Link>
        <Link href="/library">
          <button className="btn btn-ghost" style={{ padding: "12px 28px", fontSize: 15 }}>
            View Library
          </button>
        </Link>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <div className="card" style={{ padding: "24px 20px" }}>
      <div style={{ fontSize: 36, fontWeight: 800, color: accent, lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ color: "var(--text-dim)", fontSize: 13, marginTop: 6 }}>{label}</div>
    </div>
  );
}
