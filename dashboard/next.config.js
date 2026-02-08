/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // Only proxy /api/v1 to Python backend in local development
    // On Vercel, Next.js API routes handle all /api/* requests directly
    if (process.env.VERCEL) {
      return []
    }
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
    ]
  },
}

module.exports = nextConfig
