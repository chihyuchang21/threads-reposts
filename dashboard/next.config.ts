import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    SUPABASE_SERVICE_KEY: process.env.SUPABASE_SERVICE_KEY!,
  },
};

export default nextConfig;
