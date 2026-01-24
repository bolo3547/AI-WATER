import type { Metadata, Viewport } from 'next'
import './globals.css'
import { ClientLayout } from '@/components/layout/ClientLayout'

const siteUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3001'

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'AquaWatch NRW | Public Water Loss Intelligence',
    template: '%s | AquaWatch NRW'
  },
  description: 'AI-powered non-revenue water detection, leak reporting, and utility performance insights for the public and operators.',
  manifest: '/manifest.json',
  alternates: {
    canonical: '/'
  },
  openGraph: {
    type: 'website',
    url: siteUrl,
    title: 'AquaWatch NRW | Public Water Loss Intelligence',
    description: 'Track, report, and reduce non-revenue water with public transparency and operator-grade tools.',
    siteName: 'AquaWatch NRW',
    images: [
      {
        url: '/lwsc-logo.png',
        width: 512,
        height: 512,
        alt: 'AquaWatch NRW'
      }
    ]
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AquaWatch NRW | Public Water Loss Intelligence',
    description: 'Track, report, and reduce non-revenue water with public transparency and operator-grade tools.',
    images: ['/lwsc-logo.png']
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'LWSC NRW',
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: '/lwsc-logo.png', type: 'image/png' },
    ],
    apple: [
      { url: '/lwsc-logo.png' },
    ],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1
    }
  }
}

export const viewport: Viewport = {
  themeColor: '#3b82f6',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" href="/lwsc-logo.png" type="image/png" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="LWSC NRW" />
        <link rel="apple-touch-icon" href="/lwsc-logo.png" />
      </head>
      <body className="min-h-screen">
        <ClientLayout>
          {children}
        </ClientLayout>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').then(
                    function(registration) {
                      console.log('LWSC NRW: Service Worker registered', registration.scope);
                    },
                    function(err) {
                      console.log('LWSC NRW: Service Worker registration failed', err);
                    }
                  );
                });
              }
            `,
          }}
        />
      </body>
    </html>
  )
}
