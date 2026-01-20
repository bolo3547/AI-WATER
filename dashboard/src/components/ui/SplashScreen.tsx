'use client'

import { useState, useEffect } from 'react'
import { Droplets } from 'lucide-react'

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0)
  const [phase, setPhase] = useState<'rising' | 'walking' | 'complete'>('rising')

  useEffect(() => {
    // Animate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 2
      })
    }, 40)

    // Phase transitions
    const walkTimer = setTimeout(() => setPhase('walking'), 800)
    const completeTimer = setTimeout(() => {
      setPhase('complete')
      setTimeout(onComplete, 500)
    }, 2500)

    return () => {
      clearInterval(progressInterval)
      clearTimeout(walkTimer)
      clearTimeout(completeTimer)
    }
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-gradient-to-b from-blue-900 via-blue-800 to-cyan-900 overflow-hidden">
      {/* Water ripples background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Animated water waves at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-48">
          <svg className="absolute bottom-0 w-full" viewBox="0 0 1440 120" preserveAspectRatio="none">
            <path 
              className="animate-wave1"
              fill="rgba(59, 130, 246, 0.3)" 
              d="M0,64 C288,96 576,32 864,64 C1152,96 1296,32 1440,64 L1440,120 L0,120 Z"
            />
            <path 
              className="animate-wave2"
              fill="rgba(59, 130, 246, 0.2)" 
              d="M0,80 C288,48 576,112 864,80 C1152,48 1296,112 1440,80 L1440,120 L0,120 Z"
            />
            <path 
              className="animate-wave3"
              fill="rgba(6, 182, 212, 0.3)" 
              d="M0,96 C288,64 576,128 864,96 C1152,64 1296,128 1440,96 L1440,120 L0,120 Z"
            />
          </svg>
          
          {/* Water surface shimmer */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-cyan-500/20 to-transparent" />
        </div>

        {/* Floating water droplets */}
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute animate-float-up"
            style={{
              left: `${10 + (i * 8)}%`,
              bottom: '10%',
              animationDelay: `${i * 0.3}s`,
              animationDuration: `${2 + Math.random() * 2}s`
            }}
          >
            <Droplets className="w-4 h-4 text-cyan-400/40" />
          </div>
        ))}
      </div>

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Hippo/Logo animation container */}
        <div className="relative mb-8">
          {/* Water splash effect behind hippo */}
          <div 
            className={`absolute -bottom-4 left-1/2 -translate-x-1/2 transition-all duration-700 ${
              phase === 'rising' ? 'scale-150 opacity-100' : 'scale-100 opacity-60'
            }`}
          >
            <div className="w-32 h-8 bg-cyan-400/30 rounded-full blur-xl animate-pulse" />
          </div>

          {/* Hippo/Logo with walking animation */}
          <div 
            className={`relative transition-all duration-1000 ease-out ${
              phase === 'rising' 
                ? 'translate-y-8 opacity-0' 
                : phase === 'walking'
                ? 'translate-y-0 opacity-100 animate-hippo-walk'
                : 'translate-y-0 opacity-100 scale-110'
            }`}
          >
            {/* The LWSC logo with hippo */}
            <div className="relative">
              <img 
                src="/lwsc-logo.png" 
                alt="LWSC" 
                className="w-28 h-28 sm:w-36 sm:h-36 object-contain drop-shadow-2xl"
              />
              {/* Glow effect */}
              <div className="absolute inset-0 bg-cyan-400/20 rounded-full blur-2xl -z-10 animate-pulse" />
            </div>
          </div>

          {/* Water droplets splashing around */}
          {phase !== 'rising' && (
            <div className="absolute inset-0 -z-10">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="absolute animate-splash"
                  style={{
                    left: `${20 + i * 12}%`,
                    top: '80%',
                    animationDelay: `${i * 0.15}s`
                  }}
                >
                  <div className="w-2 h-2 bg-cyan-400 rounded-full" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Text */}
        <div className={`text-center transition-all duration-700 ${
          phase === 'rising' ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'
        }`}>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2 tracking-tight">
            LWSC
          </h1>
          <p className="text-cyan-300 text-sm sm:text-base font-medium tracking-wider uppercase">
            NRW Detection System
          </p>
          <p className="text-blue-300/60 text-xs mt-1">
            Lusaka Water Supply Company
          </p>
        </div>

        {/* Progress bar */}
        <div className="mt-8 w-64 sm:w-80">
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden backdrop-blur">
            <div 
              className="h-full bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 rounded-full transition-all duration-100 ease-out relative"
              style={{ width: `${progress}%` }}
            >
              {/* Shimmer effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
            </div>
          </div>
          <p className="text-center text-cyan-300/60 text-xs mt-3">
            {progress < 30 ? 'Connecting to sensors...' : 
             progress < 60 ? 'Loading AI models...' : 
             progress < 90 ? 'Preparing dashboard...' : 
             'Ready!'}
          </p>
        </div>
      </div>

      {/* Styles for animations */}
      <style jsx>{`
        @keyframes wave1 {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(-25px); }
        }
        @keyframes wave2 {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(25px); }
        }
        @keyframes wave3 {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(-15px); }
        }
        @keyframes float-up {
          0% { transform: translateY(0) scale(1); opacity: 0.4; }
          50% { opacity: 0.8; }
          100% { transform: translateY(-100px) scale(0.5); opacity: 0; }
        }
        @keyframes hippo-walk {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          25% { transform: translateY(-4px) rotate(-2deg); }
          75% { transform: translateY(-4px) rotate(2deg); }
        }
        @keyframes splash {
          0% { transform: translateY(0) scale(1); opacity: 1; }
          100% { transform: translateY(-30px) scale(0); opacity: 0; }
        }
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-wave1 { animation: wave1 3s ease-in-out infinite; }
        .animate-wave2 { animation: wave2 4s ease-in-out infinite; }
        .animate-wave3 { animation: wave3 3.5s ease-in-out infinite; }
        .animate-float-up { animation: float-up 3s ease-out infinite; }
        .animate-hippo-walk { animation: hippo-walk 0.6s ease-in-out infinite; }
        .animate-splash { animation: splash 0.8s ease-out forwards; }
        .animate-shimmer { animation: shimmer 1.5s ease-in-out infinite; }
      `}</style>
    </div>
  )
}
