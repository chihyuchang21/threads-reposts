"use client";

import { useEffect, useState, useCallback } from "react";
import ReviewCard from "@/components/review/ReviewCard";
import type { Idea } from "@/lib/types";

export default function ReviewPage() {
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [done, setDone] = useState(false);

  useEffect(() => {
    fetch("/api/ideas?status=pending")
      .then((r) => r.json())
      .then((data) => {
        setIdeas(data);
        setLoading(false);
        if (data.length === 0) setDone(true);
      });
  }, []);

  const advance = useCallback(() => {
    setIndex((i) => {
      if (i + 1 >= ideas.length) { setDone(true); return i; }
      return i + 1;
    });
  }, [ideas.length]);

  const handleApprove = useCallback(async (id: string, editedContent?: string) => {
    const body: Record<string, unknown> = { status: "approved" };
    if (editedContent) body.edited_content = editedContent;
    await fetch(`/api/ideas/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    advance();
  }, [advance]);

  const handleDelete = useCallback(async (id: string) => {
    await fetch(`/api/ideas/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "deleted" }),
    });
    advance();
  }, [advance]);

  if (loading) return <PageShell><div style={{ color: "var(--text-dim)" }}>Loading...</div></PageShell>;

  if (done || ideas.length === 0) {
    return (
      <PageShell>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✓</div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>All caught up!</h2>
          <p style={{ color: "var(--text-dim)", fontSize: 15 }}>
            {ideas.length === 0
              ? "No pending ideas. Check back after the next scrape."
              : `Reviewed all ${ideas.length} ideas.`}
          </p>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell>
      <ReviewCard
        key={ideas[index]?.id}
        idea={ideas[index]}
        index={index}
        total={ideas.length}
        onApprove={handleApprove}
        onDelete={handleDelete}
      />
    </PageShell>
  );
}

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "48px 24px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 32 }}>
        Weekly Review
      </h1>
      {children}
    </div>
  );
}
