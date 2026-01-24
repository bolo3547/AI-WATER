import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'
  const now = new Date()

  const routes = [
    '/',
    '/public',
    '/report',
    '/report-leak',
    '/track',
    '/share',
    '/portal',
    '/health',
  ]

  return routes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: now,
    changeFrequency: 'daily',
    priority: route === '/' ? 1 : 0.6
  }))
}
