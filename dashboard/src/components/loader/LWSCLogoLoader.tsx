'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'

// ============================================================
// LWSC Logo-Style Loader - Premium Authentic Animation
// Based on official LWSC emblem: Badge + Orange Sun + Blue Waves + Hippo Head
// ============================================================

export type LoaderStatus = 
  | 'auth_required'
  | 'connecting'
  | 'offline'
  | 'no_data_yet'
  | 'stale_data'
  | 'live_data'

interface LWSCLogoLoaderProps {
  status?: LoaderStatus
  mqttConnected?: boolean
  dataFresh?: boolean
  activeSensors?: number
  message?: string
  onComplete?: () => void
}

const statusMessages: Record<LoaderStatus, string> = {
  auth_required: 'Please log in…',
  connecting: 'Checking system…',
  offline: 'MQTT offline — reconnecting…',
  no_data_yet: 'Waiting for first sensor data…',
  stale_data: 'Data stale — waiting for update…',
  live_data: 'Live data connected ✓'
}

export default function LWSCLogoLoader({
  status = 'connecting',
  mqttConnected = false,
  dataFresh = false,
  activeSensors = 0,
  message,
  onComplete
}: LWSCLogoLoaderProps) {
  const prefersReducedMotion = useReducedMotion()
  const [animationPhase, setAnimationPhase] = useState<'initial' | 'rising' | 'idle' | 'complete'>('initial')
  const [showRipple, setShowRipple] = useState(false)
  const hasCompletedRef = useRef(false)

  // Calculate status based on real data (excluding connecting and auth_required which come from props)
  const effectiveStatus: LoaderStatus = (() => {
    if (status === 'auth_required') return 'auth_required'
    if (status === 'connecting') return 'connecting'
    if (!mqttConnected) return 'offline'
    if (activeSensors === 0) return 'no_data_yet'
    if (!dataFresh) return 'stale_data'
    return 'live_data'
  })()

  const displayStatus = effectiveStatus

  // Hippo rise amount based on status
  const hippoRiseY = (() => {
    switch (displayStatus) {
      case 'auth_required': return 0   // Fully hidden
      case 'connecting': return 15     // Peeking
      case 'offline': return 20        // Half out
      case 'no_data_yet': return 25    // Half out
      case 'stale_data': return 25     // Half out
      case 'live_data': return 40      // Fully risen
      default: return 15
    }
  })()

  // Animation durations (respects reduced motion)
  const waveDuration = prefersReducedMotion ? 0 : 8
  const riseDuration = prefersReducedMotion ? 0.3 : 1.8
  const breathDuration = prefersReducedMotion ? 0 : 4

  // Start rise animation
  useEffect(() => {
    const timer = setTimeout(() => setAnimationPhase('rising'), 300)
    return () => clearTimeout(timer)
  }, [])

  // Transition to idle after rise
  useEffect(() => {
    if (animationPhase === 'rising') {
      const timer = setTimeout(() => setAnimationPhase('idle'), riseDuration * 1000 + 200)
      return () => clearTimeout(timer)
    }
  }, [animationPhase, riseDuration])

  // Trigger ripple and complete when live
  useEffect(() => {
    if (displayStatus === 'live_data' && animationPhase === 'idle' && !hasCompletedRef.current) {
      hasCompletedRef.current = true
      setShowRipple(true)
      
      setTimeout(() => {
        setShowRipple(false)
        setAnimationPhase('complete')
        if (onComplete) {
          setTimeout(onComplete, 600)
        }
      }, 1200)
    }
  }, [displayStatus, animationPhase, onComplete])

  const displayMessage = message || statusMessages[displayStatus]

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-[#0a1628]">
      
      {/* Subtle ambient particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {!prefersReducedMotion && [...Array(12)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 rounded-full bg-cyan-400/20"
            style={{
              left: `${10 + Math.random() * 80}%`,
              top: `${5 + Math.random() * 35}%`,
            }}
            animate={{
              opacity: [0.1, 0.3, 0.1],
              scale: [1, 1.3, 1],
            }}
            transition={{
              duration: 3 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>

      {/* Main Logo Container */}
      <div className="relative w-64 h-64 sm:w-80 sm:h-80 md:w-96 md:h-96">
        <svg
          viewBox="0 0 200 200"
          className="w-full h-full"
          style={{ overflow: 'visible' }}
        >
          <defs>
            {/* === LWSC Brand Colors === */}
            {/* Orange Sun Gradient */}
            <radialGradient id="lwsc-sun-gradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FF8C00" />
              <stop offset="60%" stopColor="#FF6B00" />
              <stop offset="100%" stopColor="#E85D00" />
            </radialGradient>

            {/* Sun Glow */}
            <radialGradient id="lwsc-sun-glow" cx="50%" cy="50%" r="60%">
              <stop offset="0%" stopColor="#FF8C00" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#FF8C00" stopOpacity="0" />
            </radialGradient>

            {/* Blue Wave Gradient (Band 1 - Darkest/Back) */}
            <linearGradient id="lwsc-wave-1" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0066B3" />
              <stop offset="100%" stopColor="#004C8C" />
            </linearGradient>

            {/* Blue Wave Gradient (Band 2 - Medium) */}
            <linearGradient id="lwsc-wave-2" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#0088CC" />
              <stop offset="100%" stopColor="#0066B3" />
            </linearGradient>

            {/* Blue Wave Gradient (Band 3 - Lightest/Front) */}
            <linearGradient id="lwsc-wave-3" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#00AADD" />
              <stop offset="100%" stopColor="#0088CC" />
            </linearGradient>

            {/* Hippo Gradient */}
            <linearGradient id="lwsc-hippo-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#5A6672" />
              <stop offset="40%" stopColor="#4A5560" />
              <stop offset="100%" stopColor="#3A4550" />
            </linearGradient>

            {/* Badge Ring Gradient */}
            <linearGradient id="lwsc-badge-ring" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#C9A227" />
              <stop offset="50%" stopColor="#D4AF37" />
              <stop offset="100%" stopColor="#C9A227" />
            </linearGradient>

            {/* Water Ripple */}
            <radialGradient id="lwsc-ripple" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#00AADD" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#00AADD" stopOpacity="0" />
            </radialGradient>

            {/* Clip path for waves covering hippo */}
            <clipPath id="wave-clip">
              <rect x="0" y="115" width="200" height="85" />
            </clipPath>

            {/* Soft glow filter */}
            <filter id="soft-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* === OUTER BADGE RING === */}
          <motion.circle
            cx="100"
            cy="100"
            r="95"
            fill="none"
            stroke="url(#lwsc-badge-ring)"
            strokeWidth="4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
          <motion.circle
            cx="100"
            cy="100"
            r="88"
            fill="none"
            stroke="url(#lwsc-badge-ring)"
            strokeWidth="1.5"
            strokeOpacity="0.6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          />

          {/* === ORANGE SUN DISC === */}
          <motion.g>
            {/* Sun glow (subtle) */}
            <motion.circle
              cx="100"
              cy="65"
              r="38"
              fill="url(#lwsc-sun-glow)"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ 
                opacity: displayStatus === 'live_data' ? 0.5 : 0.3,
                scale: displayStatus === 'live_data' ? [1, 1.05, 1] : 1
              }}
              transition={{ 
                duration: displayStatus === 'live_data' ? 3 : 0.5,
                repeat: displayStatus === 'live_data' ? Infinity : 0,
                ease: 'easeInOut'
              }}
            />
            {/* Sun disc */}
            <motion.circle
              cx="100"
              cy="65"
              r="28"
              fill="url(#lwsc-sun-gradient)"
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.3, ease: 'easeOut' }}
            />
            {/* Sun highlight */}
            <motion.ellipse
              cx="93"
              cy="58"
              rx="8"
              ry="6"
              fill="white"
              fillOpacity="0.15"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.15 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            />
          </motion.g>

          {/* === BLUE WAVE BANDS === */}
          {/* Wave Band 1 (Back - Darkest) */}
          <motion.path
            d="M10,130 Q40,125 70,130 T130,130 T190,130 L190,165 L10,165 Z"
            fill="url(#lwsc-wave-1)"
            initial={{ opacity: 0 }}
            animate={{ 
              opacity: 1,
              d: prefersReducedMotion ? undefined : [
                "M10,130 Q40,125 70,130 T130,130 T190,130 L190,165 L10,165 Z",
                "M10,130 Q40,133 70,128 T130,132 T190,128 L190,165 L10,165 Z",
                "M10,130 Q40,125 70,130 T130,130 T190,130 L190,165 L10,165 Z",
              ]
            }}
            transition={{
              opacity: { duration: 0.5, delay: 0.4 },
              d: { duration: waveDuration, repeat: Infinity, ease: 'easeInOut' }
            }}
          />

          {/* Wave Band 2 (Middle) */}
          <motion.path
            d="M10,140 Q50,135 90,140 T170,140 T200,138 L200,175 L0,175 Z"
            fill="url(#lwsc-wave-2)"
            initial={{ opacity: 0 }}
            animate={{ 
              opacity: 1,
              d: prefersReducedMotion ? undefined : [
                "M10,140 Q50,135 90,140 T170,140 T200,138 L200,175 L0,175 Z",
                "M10,138 Q50,143 90,138 T170,142 T200,140 L200,175 L0,175 Z",
                "M10,140 Q50,135 90,140 T170,140 T200,138 L200,175 L0,175 Z",
              ]
            }}
            transition={{
              opacity: { duration: 0.5, delay: 0.5 },
              d: { duration: waveDuration * 0.9, repeat: Infinity, ease: 'easeInOut' }
            }}
          />

          {/* Wave Band 3 (Front - Lightest) */}
          <motion.path
            d="M0,150 Q30,145 60,150 T120,150 T180,150 T200,148 L200,200 L0,200 Z"
            fill="url(#lwsc-wave-3)"
            initial={{ opacity: 0 }}
            animate={{ 
              opacity: 1,
              d: prefersReducedMotion ? undefined : [
                "M0,150 Q30,145 60,150 T120,150 T180,150 T200,148 L200,200 L0,200 Z",
                "M0,148 Q30,153 60,148 T120,152 T180,148 T200,150 L200,200 L0,200 Z",
                "M0,150 Q30,145 60,150 T120,150 T180,150 T200,148 L200,200 L0,200 Z",
              ]
            }}
            transition={{
              opacity: { duration: 0.5, delay: 0.6 },
              d: { duration: waveDuration * 0.8, repeat: Infinity, ease: 'easeInOut' }
            }}
          />

          {/* === HIPPO HEAD (Rises from water) === */}
          <motion.g
            initial={{ y: 60 }}
            animate={{ 
              y: animationPhase === 'idle' || animationPhase === 'complete'
                ? (prefersReducedMotion ? 60 - hippoRiseY : [60 - hippoRiseY, 60 - hippoRiseY - 1, 60 - hippoRiseY])
                : animationPhase === 'rising' ? 60 - hippoRiseY : 60
            }}
            transition={
              animationPhase === 'idle' || animationPhase === 'complete'
                ? { duration: breathDuration, repeat: Infinity, ease: 'easeInOut' }
                : { type: 'spring', stiffness: 40, damping: 12, duration: riseDuration }
            }
          >
            {/* Hippo Head Shape */}
            <ellipse
              cx="100"
              cy="135"
              rx="32"
              ry="25"
              fill="url(#lwsc-hippo-gradient)"
            />

            {/* Hippo Snout */}
            <ellipse
              cx="100"
              cy="150"
              rx="22"
              ry="12"
              fill="#4A5560"
            />
            
            {/* Hippo Snout Highlight */}
            <ellipse
              cx="100"
              cy="147"
              rx="18"
              ry="8"
              fill="#5A6672"
              fillOpacity="0.5"
            />

            {/* Nostrils */}
            <ellipse cx="92" cy="150" rx="3.5" ry="2.5" fill="#2A3540" />
            <ellipse cx="108" cy="150" rx="3.5" ry="2.5" fill="#2A3540" />

            {/* Eyes */}
            {/* Left Eye */}
            <ellipse cx="85" cy="128" rx="7" ry="5" fill="#1A2530" />
            <ellipse cx="86" cy="127" rx="2.5" ry="2" fill="white" />
            <motion.circle
              cx="86"
              cy="127"
              r="1"
              fill="#0A1520"
              animate={!prefersReducedMotion ? { cx: [86, 87, 86] } : undefined}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            />

            {/* Right Eye */}
            <ellipse cx="115" cy="128" rx="7" ry="5" fill="#1A2530" />
            <ellipse cx="114" cy="127" rx="2.5" ry="2" fill="white" />
            <motion.circle
              cx="114"
              cy="127"
              r="1"
              fill="#0A1520"
              animate={!prefersReducedMotion ? { cx: [114, 113, 114] } : undefined}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            />

            {/* Ears */}
            <ellipse cx="72" cy="120" rx="7" ry="9" fill="#4A5560" />
            <ellipse cx="128" cy="120" rx="7" ry="9" fill="#4A5560" />
            <ellipse cx="72" cy="120" rx="4" ry="5" fill="#5A6672" fillOpacity="0.5" />
            <ellipse cx="128" cy="120" rx="4" ry="5" fill="#5A6672" fillOpacity="0.5" />

            {/* Head Highlight */}
            <ellipse cx="95" cy="130" rx="12" ry="8" fill="#6A7682" fillOpacity="0.2" />
          </motion.g>

          {/* Water Overlay (covers bottom of hippo) */}
          <motion.rect
            x="0"
            y="148"
            width="200"
            height="52"
            fill="url(#lwsc-wave-3)"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.85 }}
            transition={{ duration: 0.6, delay: 0.7 }}
          />

          {/* === RIPPLE EFFECTS === */}
          {/* Continuous subtle ripples */}
          {[0, 1].map((i) => (
            <motion.ellipse
              key={i}
              cx="100"
              cy="148"
              rx="15"
              ry="3"
              fill="none"
              stroke="#00AADD"
              strokeWidth="0.8"
              initial={{ opacity: 0 }}
              animate={!prefersReducedMotion ? {
                rx: [15, 35, 55],
                ry: [3, 5, 7],
                opacity: [0.4, 0.2, 0],
              } : undefined}
              transition={{
                duration: 3,
                delay: i * 1.5,
                repeat: Infinity,
                ease: 'easeOut'
              }}
            />
          ))}

          {/* Happy ripple when live */}
          <AnimatePresence>
            {showRipple && (
              <>
                {[0, 1, 2].map((i) => (
                  <motion.ellipse
                    key={`happy-${i}`}
                    cx="100"
                    cy="148"
                    rx="20"
                    ry="4"
                    fill="none"
                    stroke="#00DDAA"
                    strokeWidth="1.5"
                    initial={{ opacity: 0.8, rx: 20, ry: 4 }}
                    animate={{ 
                      opacity: 0, 
                      rx: 70, 
                      ry: 12 
                    }}
                    exit={{ opacity: 0 }}
                    transition={{ 
                      duration: 1,
                      delay: i * 0.2,
                      ease: 'easeOut'
                    }}
                  />
                ))}
              </>
            )}
          </AnimatePresence>

          {/* === LWSC TEXT (Top Arc) === */}
          <defs>
            <path
              id="text-arc-top"
              d="M 30,100 A 70,70 0 0,1 170,100"
              fill="none"
            />
            <path
              id="text-arc-bottom"
              d="M 170,105 A 70,70 0 0,1 30,105"
              fill="none"
            />
          </defs>
          
          <motion.text
            fill="#D4AF37"
            fontSize="9"
            fontWeight="600"
            letterSpacing="3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <textPath href="#text-arc-top" startOffset="50%" textAnchor="middle">
              LUSAKA WATER
            </textPath>
          </motion.text>

          <motion.text
            fill="#D4AF37"
            fontSize="8"
            fontWeight="500"
            letterSpacing="2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.9 }}
          >
            <textPath href="#text-arc-bottom" startOffset="50%" textAnchor="middle">
              SUPPLY COMPANY
            </textPath>
          </motion.text>
        </svg>
      </div>

      {/* === LOADING MESSAGE === */}
      <motion.div
        className="absolute bottom-16 sm:bottom-20 left-0 right-0 text-center px-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
      >
        <motion.p
          className="text-cyan-300/90 text-sm sm:text-base font-medium tracking-wide"
          animate={!prefersReducedMotion ? { opacity: [0.7, 1, 0.7] } : undefined}
          transition={{ duration: 2.5, repeat: Infinity }}
        >
          {displayMessage}
        </motion.p>

        {/* Status Indicator */}
        <div className="flex items-center justify-center gap-2 mt-3">
          <motion.span
            className={`w-2 h-2 rounded-full ${
              displayStatus === 'live_data' 
                ? 'bg-emerald-400' 
                : displayStatus === 'offline' 
                  ? 'bg-red-400' 
                  : 'bg-amber-400'
            }`}
            animate={!prefersReducedMotion ? {
              scale: [1, 1.3, 1],
              opacity: [0.6, 1, 0.6]
            } : undefined}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
          <span className={`text-xs font-medium ${
            displayStatus === 'live_data' 
              ? 'text-emerald-400' 
              : displayStatus === 'offline' 
                ? 'text-red-400' 
                : 'text-amber-400'
          }`}>
            {displayStatus === 'live_data' && `${activeSensors} sensor${activeSensors !== 1 ? 's' : ''} online`}
            {displayStatus === 'offline' && 'Reconnecting…'}
            {displayStatus === 'no_data_yet' && 'No sensors detected'}
            {displayStatus === 'stale_data' && 'Waiting for fresh data'}
            {displayStatus === 'connecting' && 'Initializing…'}
            {displayStatus === 'auth_required' && 'Authentication required'}
          </span>
        </div>
      </motion.div>

      {/* === AQUAWATCH BRANDING === */}
      <motion.div
        className="absolute top-10 sm:top-14 left-0 right-0 text-center"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
          AquaWatch
        </h1>
        <p className="text-slate-500 text-[10px] sm:text-xs mt-0.5 tracking-wider">
          NRW Detection System
        </p>
      </motion.div>
    </div>
  )
}
