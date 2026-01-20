'use client'

import { WifiOff, RefreshCw, Home, Phone, AlertTriangle } from 'lucide-react'

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-2 sm:p-4">
      <div className="max-w-md w-full">
        {/* Government Header */}
        <div className="bg-gradient-to-r from-green-700 via-emerald-600 to-orange-500 rounded-t-xl sm:rounded-t-2xl p-2.5 sm:p-4 text-white text-center">
          <p className="text-[8px] sm:text-xs opacity-80">Republic of Zambia</p>
          <h1 className="text-[10px] sm:text-sm font-bold">LUSAKA WATER SUPPLY &amp; SANITATION COMPANY</h1>
        </div>

        <div className="bg-white rounded-b-xl sm:rounded-b-2xl shadow-xl p-4 sm:p-6 md:p-8 text-center">
          {/* Offline Icon */}
          <div className="w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4 md:mb-6">
            <WifiOff className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-slate-400" />
          </div>

          <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-slate-900 mb-1 sm:mb-2">You&apos;re Offline</h2>
          <p className="text-xs sm:text-sm text-slate-500 mb-4 sm:mb-6 md:mb-8">
            No internet connection. Some features may not be available.
          </p>

          {/* Available Offline Actions */}
          <div className="bg-blue-50 rounded-lg sm:rounded-xl p-2.5 sm:p-3 md:p-4 mb-4 sm:mb-6 text-left">
            <p className="text-[10px] sm:text-xs font-semibold text-blue-700 mb-1.5 sm:mb-2 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 sm:w-4 sm:h-4" />
              Available Offline:
            </p>
            <ul className="text-[10px] sm:text-xs md:text-sm text-blue-600 space-y-0.5 sm:space-y-1">
              <li>• View cached dashboard data</li>
              <li>• Draft leak reports (sync later)</li>
              <li>• Access recent pages</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="space-y-2 sm:space-y-3">
            <button
              onClick={handleRetry}
              className="w-full flex items-center justify-center gap-1.5 sm:gap-2 py-2.5 sm:py-3 bg-blue-600 text-white rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5" />
              Try Again
            </button>

            <a
              href="/"
              className="w-full flex items-center justify-center gap-1.5 sm:gap-2 py-2.5 sm:py-3 border border-slate-200 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
            >
              <Home className="w-4 h-4 sm:w-5 sm:h-5" />
              Go to Dashboard
            </a>
          </div>

          {/* Emergency Contact */}
          <div className="mt-4 sm:mt-6 md:mt-8 pt-4 sm:pt-6 border-t border-slate-100">
            <p className="text-[10px] sm:text-xs text-slate-400 mb-1.5 sm:mb-2">For emergencies:</p>
            <a
              href="tel:+260211251778"
              className="inline-flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-red-100 text-red-700 rounded-lg font-medium text-[10px] sm:text-xs md:text-sm hover:bg-red-200 transition-colors"
            >
              <Phone className="w-3 h-3 sm:w-4 sm:h-4" />
              Call 211-251778
            </a>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[10px] sm:text-xs text-slate-400 mt-2 sm:mt-4">
          LWSC NRW Detection • Offline
        </p>
      </div>
    </div>
  )
}
