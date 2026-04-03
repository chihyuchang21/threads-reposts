import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

function serverClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
  );
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const status = searchParams.get("status") ?? "pending";
  const category = searchParams.get("category");

  let query = serverClient()
    .from("ideas")
    .select("*, repost:reposts(*)")
    .eq("status", status)
    .order("created_at", { ascending: false });

  if (category) query = query.eq("category", category);

  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}
