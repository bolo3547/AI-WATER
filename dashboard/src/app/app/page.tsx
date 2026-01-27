'use client'

import { useState, useEffect } from 'react'
import { AdminDashboard, OperatorDashboard, TechnicianDashboard } from '@/components/dashboards'
import { AppLoader } from '@/components/loader'

export default function AppDashboard() {
  const [userRole, setUserRole] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        try {
          const user = JSON.parse(userStr)
          setUserRole(user.role || 'operator')
        } catch {
          setUserRole('operator')
        }
      } else {
        setUserRole('operator')
      }
    }
    // Small delay to show the premium loader
    setTimeout(() => setIsLoading(false), 800)
  }, [])

  if (isLoading) {
    return (
      <AppLoader 
        isLoading={true}
        state="loading-dashboard"
        checkLiveStatus={true}
        minDisplayTime={1000}
      />
    )
  }

  switch (userRole) {
    case 'admin':
      return <AdminDashboard />
    case 'technician':
      return <TechnicianDashboard />
    case 'operator':
    default:
      return <OperatorDashboard />
  }
}
