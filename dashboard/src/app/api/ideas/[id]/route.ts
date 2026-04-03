import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

function serverClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const body = await req.json();
  const { status, edited_content, category } = body;

  const updates: Record<string, unknown> = {};
  if (status) {
    updates.status = status;
    updates.reviewed_at = new Date().toISOString();
  }
  if (edited_content !== undefined) updates.edited_content = edited_content;
  if (category !== undefined) updates.category = category;

  const { data, error } = await serverClient()
    .from("ideas")
    .update(updates)
    .eq("id", params.id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}
