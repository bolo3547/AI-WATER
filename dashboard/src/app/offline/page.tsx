'use client'

import { WifiOff, RefreshCw, Home, Phone, AlertTriangle } from 'lucide-react'

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Government Header */}
        <div className="bg-gradient-to-r from-green-700 via-emerald-600 to-orange-500 rounded-t-2xl p-4 text-white text-center">
          <p className="text-xs opacity-80">Republic of Zambia</p>
          <h1 className="text-sm font-bold">LUSAKA WATER SUPPLY &amp; SANITATION COMPANY</h1>
        </div>

        <div className="bg-white rounded-b-2xl shadow-xl p-8 text-center">
          {/* Offline Icon */}
          <div className="w-24 h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <WifiOff className="w-12 h-12 text-slate-400" />
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-2">You&apos;re Offline</h2>
          <p className="text-slate-500 mb-8">
            It looks like you&apos;re not connected to the internet. Some features may not be available.
          </p>

          {/* Available Offline Actions */}
          <div className="bg-blue-50 rounded-xl p-4 mb-6 text-left">
            <p className="text-xs font-semibold text-blue-700 mb-2 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" />
              Available Offline:
            </p>
            <ul className="text-sm text-blue-600 space-y-1">
              <li>• View cached dashboard data</li>
              <li>• Draft leak reports (will sync when online)</li>
              <li>• Access recently viewed pages</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <button
              onClick={handleRetry}
              className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
              Try Again
            </button>

            <a
              href="/"
              className="w-full flex items-center justify-center gap-2 py-3 border border-slate-200 rounded-xl font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              <Home className="w-5 h-5" />
              Go to Dashboard
            </a>
          </div>

          {/* Emergency Contact */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <p className="text-xs text-slate-400 mb-2">For emergencies, call directly:</p>
            <a
              href="tel:+260211251778"
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg font-medium text-sm hover:bg-red-200 transition-colors"
            >
              <Phone className="w-4 h-4" />
              Emergency: 211-251778
            </a>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-400 mt-4">
          LWSC NRW Detection System • Offline Mode
        </p>
      </div>
    </div>
  )
}
