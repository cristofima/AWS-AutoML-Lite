import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable image optimization (not needed for this app)
  images: {
    unoptimized: true,
  },
  
  // Trailing slashes for better compatibility
  trailingSlash: true,
};

export default nextConfig;
