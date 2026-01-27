'use client'

import { motion } from 'framer-motion'
import HippoSplash from '@/components/loader/HippoSplash'

export default function Loading() {
  return (
    <motion.div
      className="fixed inset-0 z-[9999] bg-slate-950"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <HippoSplash 
        isOnline={true}
        dataFresh={true}
        message="Loading AquaWatch…"
      />
    </motion.div>
  )
}
