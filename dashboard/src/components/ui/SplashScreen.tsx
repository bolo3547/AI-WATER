'use client'

import { useState, useEffect } from 'react'

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0)
  const [hippoX, setHippoX] = useState(-20) // Start from left (in water)
  const [phase, setPhase] = useState<'swimming' | 'emerging' | 'walking' | 'arrived'>('swimming')

  useEffect(() => {
    // Animate progress bar - SLOWER
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 0.8
      })
    }, 50)

    // Animate hippo walking from water to land - SLOWER
    const hippoInterval = setInterval(() => {
      setHippoX(prev => {
        if (prev >= 55) {
          clearInterval(hippoInterval)
          return 55
        }
        return prev + 0.4
      })
    }, 60)

    // Phase transitions - SLOWER timing
    setTimeout(() => setPhase('emerging'), 1000)
    setTimeout(() => setPhase('walking'), 2000)
    setTimeout(() => setPhase('arrived'), 5500)
    
    const completeTimer = setTimeout(() => {
      setTimeout(onComplete, 500)
    }, 6500)

    return () => {
      clearInterval(progressInterval)
      clearInterval(hippoInterval)
      clearTimeout(completeTimer)
    }
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center overflow-hidden">
      {/* Official Government Banner at top */}
      <div className="absolute top-0 left-0 right-0 h-8 sm:h-10 bg-gradient-to-r from-green-700 via-green-600 to-orange-500 z-10 flex items-center justify-center px-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="text-base sm:text-lg">🇿🇲</span>
          <span className="text-[10px] sm:text-xs text-white font-semibold tracking-wider">REPUBLIC OF ZAMBIA</span>
          <span className="text-[9px] sm:text-[10px] text-white/80 hidden sm:inline">| Official Government System</span>
        </div>
      </div>

      {/* Sky gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-orange-300 via-orange-400 to-blue-400" />
      
      {/* Sun */}
      <div className="absolute top-12 sm:top-16 right-3 sm:right-10 w-8 h-8 sm:w-14 sm:h-14 bg-yellow-300 rounded-full blur-sm animate-pulse" />
      <div className="absolute top-12 sm:top-16 right-3 sm:right-10 w-8 h-8 sm:w-14 sm:h-14 bg-yellow-200 rounded-full" />
      
      {/* Clouds - smaller on mobile */}
      <div className="absolute top-16 sm:top-20 left-[8%] w-10 sm:w-16 h-4 sm:h-6 bg-white/60 rounded-full blur-sm" />
      <div className="absolute top-14 sm:top-18 left-[12%] w-8 sm:w-12 h-3 sm:h-5 bg-white/50 rounded-full blur-sm" />
      <div className="absolute top-6 sm:top-16 right-[20%] w-10 sm:w-20 h-4 sm:h-8 bg-white/40 rounded-full blur-sm" />

      {/* Scene container - smaller on mobile */}
      <div className="absolute bottom-0 left-0 right-0 h-[38%] sm:h-[45%]">
        {/* Land/Beach - right side */}
        <div className="absolute bottom-0 right-0 w-[60%] h-full">
          <svg className="w-full h-full" viewBox="0 0 600 300" preserveAspectRatio="none">
            {/* Sandy beach */}
            <path d="M0,100 Q150,50 300,80 Q450,60 600,40 L600,300 L0,300 Z" fill="#E8D5A3" />
            {/* Grass on top */}
            <path d="M200,70 Q350,40 500,50 Q550,45 600,40 L600,60 Q500,55 400,60 Q300,65 200,80 Z" fill="#7CB342" />
            {/* Grass tufts */}
            <g fill="#558B2F">
              <path d="M220,75 L225,55 L230,75" />
              <path d="M260,65 L265,45 L270,65" />
              <path d="M310,60 L315,40 L320,60" />
              <path d="M380,55 L385,35 L390,55" />
              <path d="M450,50 L455,30 L460,50" />
              <path d="M520,45 L525,25 L530,45" />
            </g>
          </svg>
        </div>

        {/* Water - left side and bottom */}
        <div className="absolute bottom-0 left-0 w-full h-full">
          <svg className="w-full h-full" viewBox="0 0 1000 300" preserveAspectRatio="none">
            {/* Deep water */}
            <rect x="0" y="0" width="500" height="300" fill="#1E88E5" />
            {/* Water meeting beach */}
            <path d="M400,300 Q450,280 500,290 Q550,285 600,300 L400,300 Z" fill="#42A5F5" />
            {/* Shallow water/waves */}
            <path 
              className="animate-wave-slow"
              d="M0,180 Q100,160 200,180 Q300,200 400,180 Q450,170 500,190 L500,300 L0,300 Z" 
              fill="#42A5F5" 
            />
            <path 
              className="animate-wave-medium"
              d="M0,200 Q80,180 160,200 Q240,220 320,200 Q400,180 480,210 L500,300 L0,300 Z" 
              fill="#64B5F6" 
            />
            <path 
              className="animate-wave-fast"
              d="M0,220 Q60,200 120,220 Q180,240 240,220 Q320,200 400,230 Q450,220 500,240 L500,300 L0,300 Z" 
              fill="#90CAF9" 
            />
          </svg>
        </div>

        {/* Animated Hippo - smaller on mobile */}
        <div 
          className="absolute bottom-[20%] sm:bottom-[22%] transition-all duration-100"
          style={{ 
            left: `${hippoX}%`,
            transform: `translateX(-50%)`
          }}
        >
          <svg 
            viewBox="0 0 180 120" 
            className={`w-16 h-12 sm:w-28 sm:h-20 md:w-36 md:h-24 drop-shadow-lg ${
              phase === 'walking' ? 'animate-hippo-bob' : ''
            }`}
          >
            {/* Hippo Shadow */}
            <ellipse cx="90" cy="115" rx="50" ry="8" fill="rgba(0,0,0,0.2)" />
            
            {/* Back legs */}
            <g className={phase === 'walking' ? 'animate-leg-back' : ''}>
              <rect x="35" y="75" width="16" height="35" rx="7" fill="#6B6B6B" />
              <rect x="55" y="77" width="16" height="33" rx="7" fill="#7D7D7D" />
            </g>
            
            {/* Hippo Body */}
            <ellipse cx="85" cy="60" rx="55" ry="38" fill="#808080" />
            
            {/* Belly */}
            <ellipse cx="85" cy="70" rx="40" ry="25" fill="#9E9E9E" />
            
            {/* Front legs */}
            <g className={phase === 'walking' ? 'animate-leg-front' : ''}>
              <rect x="105" y="75" width="16" height="35" rx="7" fill="#7D7D7D" />
              <rect x="125" y="77" width="16" height="33" rx="7" fill="#6B6B6B" />
            </g>
            
            {/* Tail */}
            <path 
              d="M28 55 Q 15 50 18 65 Q 22 75 30 65" 
              fill="#808080" 
              className={phase === 'walking' ? 'animate-tail-wag' : ''}
            />
            
            {/* Hippo Head */}
            <ellipse cx="140" cy="45" rx="35" ry="30" fill="#8B8B8B" />
            
            {/* Snout */}
            <ellipse cx="168" cy="55" rx="18" ry="16" fill="#A0A0A0" />
            
            {/* Nostrils */}
            <ellipse cx="163" cy="52" rx="4" ry="3" fill="#4A4A4A" />
            <ellipse cx="175" cy="52" rx="4" ry="3" fill="#4A4A4A" />
            
            {/* Smile */}
            <path d="M158 65 Q 168 72 178 65" stroke="#5A5A5A" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            
            {/* Eyes */}
            <ellipse cx="130" cy="35" rx="8" ry="9" fill="white" />
            <ellipse cx="130" cy="36" rx="5" ry="6" fill="#2D2D2D" />
            <circle cx="128" cy="34" r="2" fill="white" />
            
            {/* Ears */}
            <ellipse cx="115" cy="20" rx="8" ry="12" fill="#8B8B8B" />
            <ellipse cx="115" cy="20" rx="4" ry="7" fill="#C4A0A0" />
            <ellipse cx="135" cy="18" rx="8" ry="12" fill="#8B8B8B" />
            <ellipse cx="135" cy="18" rx="4" ry="7" fill="#C4A0A0" />
            
            {/* Water droplets on body when emerging */}
            {(phase === 'emerging' || phase === 'walking') && (
              <g className="animate-drip">
                <circle cx="60" cy="45" r="3" fill="#87CEEB" opacity="0.8" />
                <circle cx="95" cy="40" r="2.5" fill="#87CEEB" opacity="0.7" />
                <circle cx="45" cy="60" r="2" fill="#87CEEB" opacity="0.6" />
                <circle cx="110" cy="50" r="2" fill="#87CEEB" opacity="0.7" />
              </g>
            )}
          </svg>
          
          {/* Water splash effect when in water */}
          {hippoX < 35 && (
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
              {[...Array(5)].map((_, i) => (
                <div 
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
