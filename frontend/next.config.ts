import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["172.29.16.1", "localhost", "127.0.0.1"],
};

export default nextConfig;