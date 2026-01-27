import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// =============================================================================
// ROUTE CONFIGURATION
// =============================================================================

// PUBLIC ROUTES - Accessible to everyone (citizens/public)
const publicRoutes = [
  '/',              // Landing page with news
  '/report',        // Report water issues
  '/report-leak',   // Alternative report route
  '/track',         // Track ticket status
  '/ticket',        // View ticket and chat with team
  '/news',          // Public news/updates
  '/public',        // Public information pages
]

// BACK-OFFICE ROUTES - Only for team workers (requires login)
// Access via /staff/login - not visible to public
const backofficeLoginRoute = '/staff/login'

// API routes accessible to public
const publicApiRoutes = [
  '/api/public',      // Public APIs
  '/api/report-leak', // Submit reports
  '/api/ticket',      // Ticket operations (view, chat)
  '/api/news',        // News feed
]

// API routes for authentication
const authApiRoutes = [
  '/api/auth',
]

// =============================================================================
// ROUTE MATCHING HELPERS
// =============================================================================

function isPublicRoute(pathname: string): boolean {
  return publicRoutes.some(route => 
    pathname === route || 
    pathname.startsWith(`${route}/`)
  )
}

function isPublicApiRoute(pathname: string): boolean {
  return publicApiRoutes.some(route => pathname.startsWith(route))
}

function isAuthApiRoute(pathname: string): boolean {
  return authApiRoutes.some(route => pathname.startsWith(route))
}

function isBackofficeLogin(pathname: string): boolean {
  return pathname === backofficeLoginRoute || pathname.startsWith(`${backofficeLoginRoute}/`)
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

  // Allow auth API routes
  if (isAuthApiRoute(pathname)) {
    return NextResponse.next()
  }

  // Allow back-office login page (team workers access this directly)
  if (isBackofficeLogin(pathname)) {
    return NextResponse.next()
  }

  // Block old /login route - redirect to staff login
  if (pathname === '/login') {
    return NextResponse.redirect(new URL('/staff/login', request.url))
  }

  // For all other routes (back-office), check for authentication token
  const token = request.cookies.get('access_token')?.value

  // If no token and trying to access back-office, redirect to staff login
  if (!token) {
    const loginUrl = new URL('/staff/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Token exists, allow access to back-office
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
