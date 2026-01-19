// Re-export components from Cards.tsx
export { SectionCard, AlertBanner } from './Cards'

// Additional simple UI components

interface ConfidenceIndicatorProps {
  value: number
  showLabel?: boolean
}

export function ConfidenceIndicator({ value, showLabel = false }: ConfidenceIndicatorProps) {
  const getColor = () => {
    if (value >= 90) return 'bg-emerald-500'
    if (value >= 70) return 'bg-amber-500'
    return 'bg-red-500'
  }
  
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full ${getColor()}`}
          style={{ width: `${value}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-slate-700">{value}%</span>
      )}
    </div>
  )
}
