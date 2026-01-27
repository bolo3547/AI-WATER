/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Do NOT proxy Next.js API routes - only proxy to Python backend for specific paths
      // Excluding our internal APIs: /api/public-reports/*, /api/ticket/*, etc.
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*', // Proxy to Python Backend (only /api/v1)
      },
    ]
  },
}

module.exports = nextConfig
