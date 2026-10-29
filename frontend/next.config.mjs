const backendUrl = process.env.BACKEND_URL;

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Com BACKEND_URL definida (ex.: deploy na Vercel), o /api/* é servido pela mesma origem do front.
  async rewrites() {
    if (!backendUrl) return [];
    return [{ source: "/api/:path*", destination: `${backendUrl.replace(/\/$/, "")}/api/:path*` }];
  },
};

export default nextConfig;
