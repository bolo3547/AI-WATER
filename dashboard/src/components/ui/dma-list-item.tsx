import Link from 'next/link'
import { TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react'

interface DMAListItemProps {
  rank: number
  name: string
  nrwPercent: number
  priorityScore: number
  status: 'healthy' | 'warning' | 'critical'
  trend: 'up' | 'down' | 'stable'
  href: string
}

export function DMAListItem({ 
  rank, 
  name, 
  nrwPercent, 
  priorityScore, 
  status, 
  trend,
  href 
}: DMAListItemProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200'
      case 'warning': return 'bg-amber-100 text-amber-700 border-amber-200'
      case 'healthy': return 'bg-emerald-100 text-emerald-700 border-emerald-200'
    }
  }
  
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-red-500" />
      case 'down': return <TrendingDown className="w-4 h-4 text-emerald-500" />
      case 'stable': return <Minus className="w-4 h-4 text-slate-400" />
    }
  }
  
  const getRankColor = () => {
    if (rank <= 2) return 'bg-red-500 text-white'
    if (rank <= 4) return 'bg-amber-500 text-white'
    return 'bg-slate-200 text-slate-600'
  }
  
  return (
    <Link 
      href={href}
      className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200 hover:bg-slate-100 hover:border-slate-300 transition-all group cursor-pointer"
    >
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${getRankColor()}`}>
        {rank}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-slate-900 truncate group-hover:text-blue-600 transition-colors">
            {name}
          </span>
          {getTrendIcon()}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-600">
            NRW: <span className="font-semibold">{nrwPercent.toFixed(1)}%</span>
          </span>
          <span className="text-sm text-slate-600">
            Priority: <span className="font-semibold">{priorityScore}</span>
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${getStatusColor()}`}>
          {status}
        </span>
        <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-blue-600 transition-colors" />
      </div>
    </Link>
  )
}
