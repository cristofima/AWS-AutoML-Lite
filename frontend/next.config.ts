import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable image optimization (not needed for this app)
  images: {
    unoptimized: true,
  },
  
  // Trailing slashes ensure consistent URL handling across:
  // - AWS Amplify SSR deployments (prevents 404 on refresh)
  // - Static file serving and client-side navigation
  trailingSlash: true,
};

export default nextConfig;
