import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Enable static HTML export for S3 deployment
  trailingSlash: true,  // Better compatibility with S3 website hosting
  images: {
    unoptimized: true  // Disable next/image optimization (not available in static export)
  }
};

export default nextConfig;
