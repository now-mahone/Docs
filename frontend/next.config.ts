import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: {
    turbo: {
      resolveAlias: {
        '@': './src',
      },
    },
  },
};

export default nextConfig;
