import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',
  
  // Optimize images for production
  images: {
    formats: ['image/avif', 'image/webp'],
  },
};

export default nextConfig;
