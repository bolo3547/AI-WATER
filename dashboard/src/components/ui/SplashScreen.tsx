'use client'

import { useState, useEffect } from 'react'

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0)
  const [phase, setPhase] = useState<'rising' | 'visible' | 'complete'>('rising')

  useEffect(() => {
    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 0.6
      })
    }, 40)

    // Phase transitions
    setTimeout(() => setPhase('visible'), 800)
    setTimeout(() => setPhase('complete'), 5800)
    
    const completeTimer = setTimeout(() => {
      setTimeout(onComplete, 400)
    }, 6200)

    return () => {
      clearInterval(progressInterval)
      clearTimeout(completeTimer)
    }
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-slate-900 via-blue-950 to-slate-900">
      {/* Official Government Banner at top */}
      <div className="absolute top-0 left-0 right-0 h-8 sm:h-10 bg-gradient-to-r from-green-700 via-green-600 to-orange-500 z-10 flex items-center justify-center px-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="text-base sm:text-lg">🇿🇲</span>
          <span className="text-[10px] sm:text-xs text-white font-semibold tracking-wider">REPUBLIC OF ZAMBIA</span>
          <span className="text-[9px] sm:text-[10px] text-white/80 hidden sm:inline">| Official Government System</span>
        </div>
      </div>

      {/* Animated water background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Water waves at bottom */}
        <svg className="absolute bottom-0 w-full h-40 sm:h-56" viewBox="0 0 1440 200" preserveAspectRatio="none">
          <path 
            className="animate-wave-slow"
            fill="rgba(59, 130, 246, 0.15)" 
            d="M0,100 C288,150 576,50 864,100 C1152,150 1296,50 1440,100 L1440,200 L0,200 Z"
          />
          <path 
            className="animate-wave-medium"
            fill="rgba(59, 130, 246, 0.1)" 
            d="M0,120 C288,70 576,170 864,120 C1152,70 1296,170 1440,120 L1440,200 L0,200 Z"
          />
          <path 
            className="animate-wave-fast"
            fill="rgba(6, 182, 212, 0.1)" 
            d="M0,140 C288,90 576,190 864,140 C1152,90 1296,190 1440,140 L1440,200 L0,200 Z"
          />
        </svg>
        
        {/* Subtle glow effects */}
        <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 right-1/4 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      {/* Main centered content */}
      <div className="relative z-10 flex flex-col items-center justify-center px-4">
        
        {/* Logo Container with water effect */}
        <div className={`relative transition-all duration-1000 ease-out ${
          phase === 'rising' 
            ? 'translate-y-8 opacity-0 scale-95' 
            : 'translate-y-0 opacity-100 scale-100'
        }`}>
          {/* Water ripple effect behind logo */}
          <div className="absolute -inset-8 sm:-inset-12">
            <div className="absolute inset-0 rounded-full bg-cyan-500/20 animate-ping-slow" />
            <div className="absolute inset-4 rounded-full bg-blue-500/15 animate-ping-slower" />
          </div>
          
          {/* Logo with professional border */}
          <div className="relative w-24 h-24 sm:w-32 sm:h-32 md:w-40 md:h-40 rounded-2xl bg-white p-3 sm:p-4 shadow-2xl border-4 border-blue-500/30">
            <img 
              src="/lwsc-logo.png" 
              alt="LWSC" 
              className="w-full h-full object-contain"
            />
            {/* Live indicator */}
            <div className="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-emerald-500 rounded-full border-2 border-white flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
            </div>
          </div>
        </div>

        {/* Company Name */}
        <div className={`mt-6 sm:mt-8 text-center transition-all duration-700 delay-300 ${
          phase === 'rising' ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'
        }`}>
          <h1 className="text-2xl sm:text-4xl md:text-5xl font-bold text-white tracking-tight">
            LWSC
          </h1>
          <p className="text-blue-300/90 text-xs sm:text-sm md:text-base mt-1 font-medium">
            Lusaka Water & Sewerage Company
          </p>
        </div>

        {/* System Title Badge */}
        <div className={`mt-4 sm:mt-6 transition-all duration-700 delay-500 ${
          phase === 'rising' ? 'opacity-0 scale-90' : 'opacity-100 scale-100'
        }`}>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600/30 to-cyan-600/30 rounded-full border border-blue-400/40 backdrop-blur-sm">
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
            <span className="text-cyan-300 text-xs sm:text-sm font-semibold tracking-wide">
              NRW Detection System
            </span>
            <span className="px-1.5 py-0.5 bg-cyan-500/30 rounded text-[9px] sm:text-[10px] text-cyan-200 font-bold">
              AI
            </span>
          </div>
        </div>

        {/* Features */}
        <div className={`mt-6 sm:mt-8 grid grid-cols-3 gap-3 sm:gap-6 transition-all duration-700 delay-700 ${
          phase === 'rising' ? 'opacity-0' : 'opacity-100'
        }`}>
          <div className="text-center">
            <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-2 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-[9px] sm:text-[10px] text-slate-400 font-medium">Real-time Analytics</p>
          </div>
          <div className="text-center">
            <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-2 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <p className="text-[9px] sm:text-[10px] text-slate-400 font-medium">Leak Detection</p>
          </div>
          <div className="text-center">
            <div className="w-10 h-10 sm:w-12 sm:h-12 mx-auto mb-2 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 sm:w-6 sm:h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-[9px] sm:text-[10px] text-slate-400 font-medium">Smart Automation</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className={`mt-8 sm:mt-10 w-56 sm:w-72 md:w-80 transition-all duration-700 delay-900 ${
          phase === 'rising' ? 'opacity-0' : 'opacity-100'
        }`}>
          <div className="h-1.5 sm:h-2 bg-white/10 rounded-full overflow-hidden backdrop-blur">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-500 rounded-full transition-all duration-100 ease-out relative"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
            </div>
          </div>
          <p className="text-center text-slate-400 text-[10px] sm:text-xs mt-3 font-medium">
            {progress < 20 ? 'Initializing system...' : 
             progress < 40 ? 'Connecting to sensors...' : 
             progress < 60 ? 'Loading AI models...' : 
             progress < 80 ? 'Preparing dashboard...' : 
             progress < 100 ? 'Almost ready...' :
             '✓ System Ready'}
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="absolute bottom-4 sm:bottom-6 left-0 right-0 text-center">
        <p className="text-slate-500 text-[9px] sm:text-[10px]">
          © 2026 LWSC | Powered by AI Technology
        </p>
      </div>

      {/* Styles for animations */}
      <style jsx>{`
        @keyframes wave-slow {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(-30px); }
        }
        @keyframes wave-medium {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(30px); }
        }
        @keyframes wave-fast {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(-20px); }
        }
        @keyframes ping-slow {
          0% { transform: scale(1); opacity: 0.3; }
          75%, 100% { transform: scale(1.5); opacity: 0; }
        }
        @keyframes ping-slower {
          0% { transform: scale(1); opacity: 0.2; }
          75%, 100% { transform: scale(1.8); opacity: 0; }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-wave-slow { animation: wave-slow 4s ease-in-out infinite; }
        .animate-wave-medium { animation: wave-medium 3s ease-in-out infinite; }
        .animate-wave-fast { animation: wave-fast 2.5s ease-in-out infinite; }
        .animate-ping-slow { animation: ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite; }
        .animate-ping-slower { animation: ping-slower 2.5s cubic-bezier(0, 0, 0.2, 1) infinite; }
        .animate-shimmer { animation: shimmer 2s ease-in-out infinite; }
      `}</style>
    </div>
  )
} 
                  key={i} 
                  className="w-2 h-2 bg-blue-300 rounded-full animate-splash-up"
                  style={{ animationDelay: `${i * 0.1}s` }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Text overlay - positioned better for mobile */}
      <div className={`absolute top-[8%] sm:top-[12%] left-1/2 -translate-x-1/2 text-center transition-all duration-700 ${
        phase === 'swimming' ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'
      }`}>
        <h1 className="text-xl sm:text-3xl md:text-4xl font-bold text-white mb-0.5 sm:mb-1 tracking-tight drop-shadow-lg">
          LWSC
        </h1>
        <p className="text-white/90 text-[10px] sm:text-sm md:text-base font-medium tracking-wider uppercase drop-shadow">
          NRW Detection System
        </p>
        <p className="text-white/60 text-[9px] sm:text-xs mt-0.5 drop-shadow">
          Lusaka Water Supply Company
        </p>
      </div>

      {/* Progress bar at bottom - compact on mobile */}
      <div className="absolute bottom-3 sm:bottom-8 left-1/2 -translate-x-1/2 w-40 sm:w-64 md:w-72">
        <div className="h-1.5 sm:h-2 bg-white/20 rounded-full overflow-hidden backdrop-blur">
          <div 
            className="h-full bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 rounded-full transition-all duration-100 ease-out relative"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
          </div>
        </div>
        <p className="text-center text-white/70 text-[9px] sm:text-xs mt-1.5 sm:mt-2 font-medium drop-shadow">
          {progress < 25 ? 'Hippo swimming...' : 
           progress < 50 ? 'Emerging from water...' : 
           progress < 80 ? 'Walking to shore...' : 
           progress < 100 ? 'Almost there...' :
           'Ready!'}
        </p>
      </div>

      {/* Styles for animations */}
      <style jsx>{`
        @keyframes wave-slow {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(-20px); }
        }
        @keyframes wave-medium {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(15px); }
        }
        @keyframes wave-fast {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(-10px); }
        }
        @keyframes hippo-bob {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        @keyframes leg-front {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(15deg); }
          75% { transform: rotate(-15deg); }
        }
        @keyframes leg-back {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(-15deg); }
          75% { transform: rotate(15deg); }
        }
        @keyframes tail-wag {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(20deg); }
        }
        @keyframes splash-up {
          0% { transform: translateY(0) scale(1); opacity: 1; }
          100% { transform: translateY(-20px) scale(0.5); opacity: 0; }
        }
        @keyframes drip {
          0%, 50% { opacity: 0.8; transform: translateY(0); }
          100% { opacity: 0; transform: translateY(10px); }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-wave-slow { animation: wave-slow 3s ease-in-out infinite; }
        .animate-wave-medium { animation: wave-medium 2.5s ease-in-out infinite; }
        .animate-wave-fast { animation: wave-fast 2s ease-in-out infinite; }
        .animate-hippo-bob { animation: hippo-bob 0.4s ease-in-out infinite; }
        .animate-leg-front { animation: leg-front 0.4s ease-in-out infinite; transform-origin: top center; }
        .animate-leg-back { animation: leg-back 0.4s ease-in-out infinite; transform-origin: top center; }
        .animate-tail-wag { animation: tail-wag 0.5s ease-in-out infinite; transform-origin: right center; }
        .animate-splash-up { animation: splash-up 0.6s ease-out infinite; }
        .animate-drip { animation: drip 1.5s ease-out infinite; }
        .animate-shimmer { animation: shimmer 1.5s ease-in-out infinite; }
      `}</style>
    </div>
  )
}
