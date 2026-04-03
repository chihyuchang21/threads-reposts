import { createClient } from "@supabase/supabase-js";
import type { Idea } from "@/lib/types";

function serverClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

async function getApprovedIdeas(category?: string): Promise<Idea[]> {
  let q = serverClient()
    .from("ideas")
    .select("*, repost:reposts(*)")
    .eq("status", "approved")
    .order("created_at", { ascending: false });
  if (category) q = q.eq("category", category);
  const { data } = await q;
  return (data ?? []) as Idea[];
}

async function getCategories(): Promise<string[]> {
  const { data } = await serverClient()
    .from("ideas")
    .select("category")
    .eq("status", "approved")
    .not("category", "is", null);
  const all = (data ?? []).map((r: { category: string | null }) => r.category).filter(Boolean);
  return [...new Set(all)] as string[];
}

export default async function LibraryPage({
  searchParams,
}: {
  searchParams: { category?: string };
}) {
  const activeCategory = searchParams.category;
  const [ideas, categories] = await Promise.all([
    getApprovedIdeas(activeCategory),
    getCategories(),
  ]);

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "48px 24px" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 32, flexWrap: "wrap" }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Library</h1>
        <span style={{ color: "var(--text-dim)", fontSize: 14 }}>
          {ideas.length} ideas saved
        </span>
      </div>

      {/* Category filter */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 32 }}>
        <FilterChip label="All" href="/library" active={!activeCategory} />
        {categories.map((c) => (
          <FilterChip key={c} label={c} href={`/library?category=${encodeURIComponent(c)}`} active={c === activeCategory} />
        ))}
      </div>

      {ideas.length === 0 ? (
        <p style={{ color: "var(--text-dim)" }}>No ideas yet. Go do a Review session first!</p>
      ) : (
        <div style={{ columns: "280px 3", gap: 16 }}>
          {ideas.map((idea) => (
            <IdeaCard key={idea.id} idea={idea} />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterChip({ label, href, active }: { label: string; href: string; active: boolean }) {
  return (
    <a
      href={href}
      style={{
        display: "inline-block",
        padding: "5px 14px",
        borderRadius: 99,
        fontSize: 13,
        fontWeight: 500,
        textDecoration: "none",
        border: "1px solid",
        borderColor: active ? "var(--accent)" : "var(--border)",
        background: active ? "rgba(124,111,255,0.12)" : "transparent",
        color: active ? "var(--accent)" : "var(--text-dim)",
        transition: "all 0.15s",
      }}
    >
      {label}
    </a>
  );
}

function IdeaCard({ idea }: { idea: Idea }) {
  const content = idea.edited_content ?? idea.content;
  const date = new Date(idea.created_at).toLocaleDateString("zh-TW", {
    month: "short",
    day: "numeric",
  });

  return (
    <div
      className="card"
      style={{
        padding: "20px",
        breakInside: "avoid",
        marginBottom: 16,
        display: "inline-block",
        width: "100%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8, marginBottom: 12 }}>
        {idea.category && <span className="tag">{idea.category}</span>}
        <span style={{ fontSize: 11, color: "var(--text-dim)", flexShrink: 0, marginLeft: "auto" }}>
          {date}
        </span>
      </div>

      <p style={{ fontSize: 14, lineHeight: 1.65, fontWeight: 500, marginBottom: 12 }}>
        {content}
      </p>

      {idea.extended_thoughts?.length > 0 && (
        <ul style={{ paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
          {(idea.extended_thoughts as string[]).map((q: string, i: number) => (
            <li key={i} style={{ fontSize: 12, color: "var(--text-dim)", display: "flex", gap: 6 }}>
              <span style={{ color: "var(--accent)", flexShrink: 0 }}>·</span>
              {q}
            </li>
          ))}
        </ul>
      )}

      <div style={{ marginTop: 12, fontSize: 11, color: "var(--muted)" }}>
        via @{idea.repost?.original_author}
      </div>
    </div>
  );
}
