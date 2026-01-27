'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'

interface HippoSplashProps {
  isOnline?: boolean
  dataFresh?: boolean
  message?: string
  onComplete?: () => void
}

export default function HippoSplash({ 
  isOnline = true, 
  dataFresh = true, 
  message = "Loading AquaWatch…",
  onComplete 
}: HippoSplashProps) {
  const prefersReducedMotion = useReducedMotion()
  const [animationPhase, setAnimationPhase] = useState<'rising' | 'idle' | 'complete'>('rising')
  const [showHappyRipple, setShowHappyRipple] = useState(false)
  const hasCompletedRef = useRef(false)

  // Determine target position based on sensor status
  const targetY = isOnline && dataFresh ? -45 : -25 // Full rise vs half rise
  const animationDuration = prefersReducedMotion ? 0.3 : 1.5

  useEffect(() => {
    if (isOnline && dataFresh && animationPhase === 'idle') {
      // Sensors came online - trigger happy ripple
      setShowHappyRipple(true)
      setTimeout(() => setShowHappyRipple(false), 1000)
    }
  }, [isOnline, dataFresh, animationPhase])

  useEffect(() => {
    // Set idle after initial rise
    const timer = setTimeout(() => {
      setAnimationPhase('idle')
    }, animationDuration * 1000 + 200)
    
    return () => clearTimeout(timer)
  }, [animationDuration])

  useEffect(() => {
    // Auto-complete when online and fresh
    if (isOnline && dataFresh && animationPhase === 'idle' && !hasCompletedRef.current) {
      hasCompletedRef.current = true
      const completeTimer = setTimeout(() => {
        setAnimationPhase('complete')
        if (onComplete) {
          setTimeout(onComplete, 500)
        }
      }, 800)
      return () => clearTimeout(completeTimer)
    }
  }, [isOnline, dataFresh, animationPhase, onComplete])

  // Ripple animation variants
  const rippleVariants = {
    initial: { scale: 0.8, opacity: 0.6 },
    animate: (i: number) => ({
      scale: [0.8, 1.5 + i * 0.3, 2 + i * 0.5],
      opacity: [0.6, 0.3, 0],
      transition: {
        duration: prefersReducedMotion ? 0.5 : 2,
        delay: i * 0.3,
        repeat: Infinity,
        ease: "easeOut" as const
      }
    })
  }

  // Happy ripple for when sensors connect
  const happyRippleVariants = {
    initial: { scale: 1, opacity: 0.8 },
    animate: {
      scale: [1, 2.5, 4],
      opacity: [0.8, 0.4, 0],
      transition: { duration: 0.8, ease: "easeOut" as const }
    }
  }

  // Breathing animation for idle state
  const breathingVariants = {
    idle: {
      y: [targetY, targetY - 2, targetY],
      transition: {
        duration: prefersReducedMotion ? 0 : 3,
        repeat: Infinity,
        ease: "easeInOut" as const
      }
    }
  }

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-cyan-950" />
      
      {/* Stars/particles in background */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-white/20 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 40}%`,
            }}
            animate={{
              opacity: [0.2, 0.5, 0.2],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 2 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>

      {/* Main animation container */}
      <div className="relative w-72 h-72 sm:w-96 sm:h-96">
        <svg 
          viewBox="0 0 200 200" 
          className="w-full h-full"
          style={{ overflow: 'visible' }}
        >
          <defs>
            {/* Water gradient */}
            <linearGradient id="waterGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0891b2" stopOpacity="0.9" />
              <stop offset="50%" stopColor="#0e7490" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#155e75" stopOpacity="1" />
            </linearGradient>
            
            {/* Water surface highlight */}
            <linearGradient id="waterSurface" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#0891b2" stopOpacity="0" />
            </linearGradient>

            {/* Hippo gradient */}
            <linearGradient id="hippoGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#64748b" />
              <stop offset="50%" stopColor="#475569" />
              <stop offset="100%" stopColor="#334155" />
            </linearGradient>

            {/* Ripple gradient */}
            <radialGradient id="rippleGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
            </radialGradient>

            {/* Clip mask for water */}
            <clipPath id="waterClip">
              <rect x="0" y="100" width="200" height="100" />
            </clipPath>

            {/* Glow filter */}
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Water body */}
          <rect 
            x="0" y="100" 
            width="200" height="100" 
            fill="url(#waterGradient)"
          />
          
          {/* Animated water waves */}
          <motion.path
            d="M0,100 Q25,95 50,100 T100,100 T150,100 T200,100 L200,200 L0,200 Z"
            fill="url(#waterGradient)"
            animate={{
              d: [
                "M0,100 Q25,95 50,100 T100,100 T150,100 T200,100 L200,200 L0,200 Z",
                "M0,100 Q25,105 50,100 T100,100 T150,100 T200,100 L200,200 L0,200 Z",
                "M0,100 Q25,95 50,100 T100,100 T150,100 T200,100 L200,200 L0,200 Z",
              ]
            }}
            transition={{
              duration: prefersReducedMotion ? 0 : 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />

          {/* Water surface shine */}
          <motion.ellipse
            cx="100"
            cy="100"
            rx="80"
            ry="3"
            fill="url(#waterSurface)"
            animate={{
              rx: [80, 85, 80],
              opacity: [0.4, 0.6, 0.4]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />

          {/* Ripples */}
          {[0, 1, 2].map((i) => (
            <motion.ellipse
              key={i}
              cx="100"
              cy="100"
              rx="20"
              ry="5"
              fill="none"
              stroke="#22d3ee"
              strokeWidth="1"
              strokeOpacity="0.5"
              variants={rippleVariants}
              initial="initial"
              animate="animate"
              custom={i}
            />
          ))}

          {/* Happy ripple when sensors connect */}
          <AnimatePresence>
            {showHappyRipple && (
              <motion.ellipse
                cx="100"
                cy="100"
                rx="30"
                ry="8"
                fill="none"
                stroke="#22d3ee"
                strokeWidth="2"
                variants={happyRippleVariants}
                initial="initial"
                animate="animate"
                exit={{ opacity: 0 }}
              />
            )}
          </AnimatePresence>

          {/* Hippo head group */}
          <motion.g
            initial={{ y: 60 }}
            animate={{ 
              y: animationPhase === 'idle' 
                ? [targetY, targetY - 2, targetY] 
                : targetY 
            }}
            transition={animationPhase === 'idle' 
              ? {
                  duration: prefersReducedMotion ? 0 : 3,
                  repeat: Infinity,
                  ease: "easeInOut" as const
                }
              : {
                  type: "spring",
                  stiffness: 50,
                  damping: 15,
                  duration: animationDuration
                }
            }
          >
            {/* Hippo head main shape */}
            <ellipse 
              cx="100" cy="120" 
              rx="35" ry="28" 
              fill="url(#hippoGradient)"
              filter="url(#glow)"
            />
            
            {/* Hippo snout */}
            <ellipse 
              cx="100" cy="138" 
              rx="25" ry="15" 
              fill="#475569"
            />
            
            {/* Nostrils */}
            <ellipse cx="92" cy="138" rx="4" ry="3" fill="#1e293b" />
            <ellipse cx="108" cy="138" rx="4" ry="3" fill="#1e293b" />
            
            {/* Eyes */}
            <g>
              {/* Left eye */}
              <ellipse cx="85" cy="110" rx="8" ry="6" fill="#1e293b" />
              <ellipse cx="86" cy="109" rx="3" ry="2.5" fill="white" />
              <motion.ellipse 
                cx="86" cy="109" 
                rx="1.5" ry="1.5" 
                fill="#0f172a"
                animate={{
                  cx: isOnline ? [86, 87, 86] : 86
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
              
              {/* Right eye */}
              <ellipse cx="115" cy="110" rx="8" ry="6" fill="#1e293b" />
              <ellipse cx="114" cy="109" rx="3" ry="2.5" fill="white" />
              <motion.ellipse 
                cx="114" cy="109" 
                rx="1.5" ry="1.5" 
                fill="#0f172a"
                animate={{
                  cx: isOnline ? [114, 113, 114] : 114
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              />
            </g>
            
            {/* Ears */}
            <ellipse cx="70" cy="100" rx="8" ry="10" fill="#475569" />
            <ellipse cx="130" cy="100" rx="8" ry="10" fill="#475569" />
            <ellipse cx="70" cy="100" rx="4" ry="5" fill="#64748b" />
            <ellipse cx="130" cy="100" rx="4" ry="5" fill="#64748b" />

            {/* Subtle highlights on head */}
            <ellipse cx="90" cy="115" rx="15" ry="8" fill="#64748b" opacity="0.3" />
          </motion.g>

          {/* Water overlay (covers bottom of hippo when submerged) */}
          <rect 
            x="0" y="105" 
            width="200" height="95" 
            fill="url(#waterGradient)"
            opacity="0.7"
          />

          {/* Front ripples (appear in front of hippo) */}
          <motion.ellipse
            cx="100"
            cy="105"
            rx="40"
            ry="4"
            fill="none"
            stroke="#22d3ee"
            strokeWidth="0.5"
            strokeOpacity="0.3"
            animate={{
              rx: [40, 50, 40],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        </svg>
      </div>

      {/* Loading message */}
      <motion.div
        className="absolute bottom-12 sm:bottom-16 left-0 right-0 text-center"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.5 }}
      >
        <motion.p 
          className="text-cyan-300 text-sm sm:text-base font-medium tracking-wide"
          animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {message}
        </motion.p>
        
        {/* Status indicator */}
        <div className="flex items-center justify-center gap-2 mt-3">
          <motion.span
            className={`w-2 h-2 rounded-full ${isOnline && dataFresh ? 'bg-emerald-400' : 'bg-amber-400'}`}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.7, 1, 0.7]
            }}
            transition={{ duration: 1, repeat: Infinity }}
          />
          <span className={`text-xs ${isOnline && dataFresh ? 'text-emerald-400' : 'text-amber-400'}`}>
            {isOnline && dataFresh ? 'Live data connected ✓' : 'Waiting for sensors…'}
          </span>
        </div>
      </motion.div>

      {/* AquaWatch branding */}
      <motion.div
        className="absolute top-8 sm:top-12 left-0 right-0 text-center"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
          AquaWatch
        </h1>
        <p className="text-slate-500 text-xs mt-1">Smart Water Intelligence</p>
      </motion.div>
    </div>
  )
}
