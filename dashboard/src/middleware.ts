import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that are publicly accessible (no login required)
const publicRoutes = [
  '/',
  '/login',
  '/portal',
  '/report',
  '/report-leak',
  '/track',
  '/share',
  '/public',
  '/r',  // Public referral/share links
]

// API routes that don't require authentication
const publicApiRoutes = [
  '/api/public',
  '/api/auth',
  '/api/report-leak',
]

// Check if a path matches any of the public routes
function isPublicRoute(pathname: string): boolean {
  // Exact match or starts with public route prefix
  return publicRoutes.some(route => 
    pathname === route || 
    pathname.startsWith(`${route}/`) ||
    pathname.startsWith('/public/')
  )
}

// Check if it's a public API route
function isPublicApiRoute(pathname: string): boolean {
  return publicApiRoutes.some(route => pathname.startsWith(route))
}

// Check if it's a static file or Next.js internal route
function isStaticOrInternal(pathname: string): boolean {
  return (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/static/') ||
    pathname.startsWith('/icons/') ||
    pathname.includes('.') || // Files with extensions (images, etc.)
    pathname === '/favicon.ico' ||
    pathname === '/manifest.json' ||
    pathname === '/sw.js' ||
    pathname === '/offline.html'
  )
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Allow static files and Next.js internal routes
  if (isStaticOrInternal(pathname)) {
    return NextResponse.next()
  }

  // Allow public routes without authentication
  if (isPublicRoute(pathname)) {
    return NextResponse.next()
  }

  // Allow public API routes
  if (isPublicApiRoute(pathname)) {
    return NextResponse.next()
  }

  // For protected routes, check for authentication token
  // Note: In Next.js middleware, we check cookies (not localStorage)
  const token = request.cookies.get('access_token')?.value

  // If no token and trying to access protected route, redirect to login
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Token exists, allow access
  // Note: For production, you should validate the JWT token here
  return NextResponse.next()
}

// Configure which routes the middleware applies to
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
