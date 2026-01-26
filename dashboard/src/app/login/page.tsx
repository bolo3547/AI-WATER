'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Shield, Eye, EyeOff, Lock, CheckCircle2 } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // Check if already logged in
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) {
        router.replace('/app')
      }
    }
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Call MongoDB-backed login API
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Login failed')
      }

      // Store token and user info in localStorage (for client-side access)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      
      // Also store token in cookie (for server-side middleware protection)
      // HttpOnly is set to false so we can also clear it from client-side on logout
      document.cookie = `access_token=${data.access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Strict`

      // Force redirect to dashboard
      window.location.href = '/app'
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex flex-col">
      {/* Official Government Header Banner */}
      <div className="bg-gradient-to-r from-green-700 via-green-600 to-orange-500 text-white py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Zambia Coat of Arms placeholder */}
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-white/20 rounded-full flex items-center justify-center">
              <span className="text-lg sm:text-xl">🇿🇲</span>
            </div>
            <div className="hidden sm:block">
              <p className="text-[10px] sm:text-xs font-semibold tracking-wider uppercase">Republic of Zambia</p>
              <p className="text-[9px] sm:text-[10px] opacity-80">Ministry of Water Development & Sanitation</p>
            </div>
            <p className="sm:hidden text-xs font-semibold">Republic of Zambia</p>
          </div>
          <div className="text-right">
            <p className="text-[9px] sm:text-[10px] opacity-80">Official Government System</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        {/* Background effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-3xl"></div>
        </div>

        <div className="relative w-full max-w-md">
          {/* Logo and Title */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-white mb-4 shadow-2xl p-2 border-4 border-blue-500/20">
              <img src="/lwsc-logo.png" alt="LWSC" className="w-full h-full object-contain" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-1">LWSC</h1>
            <p className="text-blue-200/80 text-xs sm:text-sm">Lusaka Water & Sewerage Company</p>
            <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 bg-blue-500/20 rounded-full border border-blue-400/30">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
              <p className="text-cyan-300 text-[10px] sm:text-xs font-medium">AI-Powered NRW Detection System</p>
            </div>
          </div>

          {/* Login Card */}
          <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6 sm:p-8 shadow-2xl">
            {/* Security Badge */}
            <div className="flex items-center justify-center gap-2 mb-5 sm:mb-6">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
                <Shield className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-semibold text-emerald-400">Secure Portal</span>
                <Lock className="w-3 h-3 text-emerald-400" />
              </div>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error}
                </div>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4 sm:space-y-5">
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-300 mb-2">Username / Employee ID</label>
                <div className="relative">
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-4 py-2.5 sm:py-3 pl-10 sm:pl-11 rounded-xl bg-white/10 border border-white/20 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                    placeholder="Enter your username"
                    required
                  />
                  <svg className="absolute left-3 sm:left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>

              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-300 mb-2">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2.5 sm:py-3 pl-10 sm:pl-11 pr-10 sm:pr-11 rounded-xl bg-white/10 border border-white/20 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm"
                    placeholder="Enter your password"
                    required
                  />
                  <svg className="absolute left-3 sm:left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 sm:right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4 sm:w-5 sm:h-5" /> : <Eye className="w-4 h-4 sm:w-5 sm:h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs sm:text-sm">
                <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                  <input type="checkbox" className="w-3.5 h-3.5 sm:w-4 sm:h-4 rounded border-slate-500 bg-white/10 text-blue-500 focus:ring-blue-500/50" />
                  Remember me
                </label>
                <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 sm:py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold hover:from-blue-500 hover:to-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/25 text-sm sm:text-base"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Authenticating...
                  </span>
                ) : (
                  'Sign In to Portal'
                )}
              </button>
            </form>

            {/* Security Features */}
            <div className="mt-5 sm:mt-6 pt-4 sm:pt-5 border-t border-white/10">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="flex flex-col items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-[9px] sm:text-[10px] text-slate-400">256-bit SSL</span>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-[9px] sm:text-[10px] text-slate-400">GDPR Compliant</span>
                </div>
                <div className="flex flex-col items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-[9px] sm:text-[10px] text-slate-400">ISO 27001</span>
                </div>
              </div>
            </div>
          </div>

          {/* Support Contact */}
          <div className="mt-4 p-3 bg-white/5 rounded-xl border border-white/10">
            <p className="text-[10px] sm:text-xs text-slate-400 text-center">
              <span className="font-medium text-slate-300">Technical Support:</span> +260 211 250 155 | support@lwsc.com.zm
            </p>
          </div>

          {/* Footer */}
          <div className="text-center mt-4 sm:mt-6 space-y-1.5 sm:space-y-2">
            <p className="text-slate-400 text-[10px] sm:text-xs">
              © 2026 Lusaka Water & Sewerage Company. All rights reserved.
            </p>
            <p className="text-slate-500 text-[9px] sm:text-[10px]">
              A Government of the Republic of Zambia Enterprise
            </p>
            <div className="flex items-center justify-center gap-3 text-[9px] sm:text-[10px] text-slate-500">
              <a href="#" className="hover:text-blue-400 transition-colors">Privacy Policy</a>
              <span>•</span>
              <a href="#" className="hover:text-blue-400 transition-colors">Terms of Use</a>
              <span>•</span>
              <a href="#" className="hover:text-blue-400 transition-colors">Accessibility</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
