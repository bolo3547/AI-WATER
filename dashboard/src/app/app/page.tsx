'use client'

import { useState, useEffect } from 'react'
import { AdminDashboard, OperatorDashboard, TechnicianDashboard } from '@/components/dashboards'

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
    setIsLoading(false)
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
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
