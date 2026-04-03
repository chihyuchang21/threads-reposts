"use client";

import { useState } from "react";
import type { Idea } from "@/lib/types";

interface Props {
  idea: Idea;
  index: number;
  total: number;
  onApprove: (id: string, editedContent?: string) => void;
  onDelete: (id: string) => void;
}

export default function ReviewCard({ idea, index, total, onApprove, onDelete }: Props) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(idea.content);
  const [loading, setLoading] = useState(false);

  const displayContent = idea.edited_content ?? idea.content;

  async function handleApprove() {
    setLoading(true);
    await onApprove(idea.id, editing ? editText : undefined);
    setLoading(false);
  }

  async function handleDelete() {
    setLoading(true);
    await onDelete(idea.id);
    setLoading(false);
  }

  return (
    <div className="card" style={{ padding: "32px", maxWidth: 680, margin: "0 auto" }}>
      {/* Progress */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 28 }}>
        <span style={{ fontSize: 13, color: "var(--text-dim)", fontVariantNumeric: "tabular-nums" }}>
          {index + 1} / {total}
        </span>
        <div style={{ flex: 1, height: 3, background: "var(--border)", borderRadius: 99 }}>
          <div
            style={{
              height: "100%",
              width: `${((index + 1) / total) * 100}%`,
              background: "var(--accent)",
              borderRadius: 99,
              transition: "width 0.3s",
            }}
          />
        </div>
      </div>

      {/* Original Post */}
      <div style={{ marginBottom: 24 }}>
        <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-dim)", textTransform: "uppercase" }}>
          Original Post
        </label>
        <div style={{ marginTop: 8, color: "var(--text-dim)", fontSize: 13 }}>
          @{idea.repost?.original_author}
        </div>
        <div
          style={{
            marginTop: 8,
            padding: "14px 16px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 14,
            lineHeight: 1.65,
            color: "var(--text-dim)",
            maxHeight: 120,
            overflowY: "auto",
          }}
        >
          {idea.repost?.original_content}
        </div>
      </div>

      {/* Extracted Idea */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-dim)", textTransform: "uppercase" }}>
          Extracted Idea
        </label>
        {editing ? (
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            style={{
              width: "100%",
              marginTop: 10,
              padding: "12px 14px",
              background: "var(--bg)",
              border: "1px solid var(--accent)",
              borderRadius: 8,
              color: "var(--text)",
              fontSize: 15,
              lineHeight: 1.6,
              resize: "vertical",
              minHeight: 100,
              outline: "none",
            }}
          />
        ) : (
          <p style={{ marginTop: 10, fontSize: 16, lineHeight: 1.65, fontWeight: 500 }}>
            {displayContent}
          </p>
        )}
      </div>

      {/* Category */}
      {idea.category && (
        <div style={{ marginBottom: 20 }}>
          <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-dim)", textTransform: "uppercase" }}>
            Category
          </label>
          <div style={{ marginTop: 8 }}>
            <span className="tag">{idea.category}</span>
          </div>
        </div>
      )}

      {/* Think Deeper */}
      {idea.extended_thoughts?.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-dim)", textTransform: "uppercase" }}>
            Think Deeper
          </label>
          <ul style={{ marginTop: 10, paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6 }}>
            {(idea.extended_thoughts as string[]).map((q: string, i: number) => (
              <li key={i} style={{ fontSize: 13, color: "var(--text-dim)", display: "flex", gap: 8 }}>
                <span style={{ color: "var(--accent)", flexShrink: 0 }}>·</span>
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          className="btn btn-keep"
          onClick={handleApprove}
          disabled={loading}
        >
          ✓ Keep
        </button>
        <button
          className="btn btn-edit"
          onClick={() => {
            setEditing(!editing);
            if (editing) setEditText(displayContent);
          }}
        >
          {editing ? "Cancel" : "✏ Edit"}
        </button>
        {editing && (
          <button className="btn btn-keep" onClick={handleApprove} disabled={loading}>
            Save & Keep
          </button>
        )}
        <button
          className="btn btn-skip"
          onClick={handleDelete}
          disabled={loading}
        >
          ✕ Skip
        </button>
      </div>
    </div>
  );
}
