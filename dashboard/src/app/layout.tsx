import type { Metadata, Viewport } from 'next'
import './globals.css'
import { ClientLayout } from '@/components/layout/ClientLayout'

export const metadata: Metadata = {
  title: 'LWSC NRW Detection System',
  description: 'AI-Powered Non-Revenue Water Detection and Management System for Lusaka Water Supply Company',
  manifest: '/manifest.json',
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
