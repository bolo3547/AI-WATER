'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface TooltipProviderProps {
  children: React.ReactNode
  delayDuration?: number
}

const TooltipProvider: React.FC<TooltipProviderProps> = ({ children }) => {
  return <>{children}</>
}

interface TooltipProps {
  children: React.ReactNode
  open?: boolean
  defaultOpen?: boolean
  onOpenChange?: (open: boolean) => void
}

const Tooltip: React.FC<TooltipProps> = ({ children }) => {
  return <div className="relative inline-block">{children}</div>
}

interface TooltipTriggerProps extends React.HTMLAttributes<HTMLDivElement> {
  asChild?: boolean
}

const TooltipTrigger = React.forwardRef<HTMLDivElement, TooltipTriggerProps>(
  ({ className, asChild, children, ...props }, ref) => {
    const [showTooltip, setShowTooltip] = React.useState(false)
    
    const child = asChild && React.isValidElement(children) 
      ? React.cloneElement(children as React.ReactElement<any>, {
          onMouseEnter: () => setShowTooltip(true),
          onMouseLeave: () => setShowTooltip(false),
          'data-tooltip-open': showTooltip
        })
      : (
          <div
            ref={ref}
            className={cn("inline-block", className)}
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
            data-tooltip-open={showTooltip}
            {...props}
          >
            {children}
          </div>
        )
    
    return child
  }
)
TooltipTrigger.displayName = 'TooltipTrigger'

interface TooltipContentProps extends React.HTMLAttributes<HTMLDivElement> {
  side?: 'top' | 'bottom' | 'left' | 'right'
  sideOffset?: number
}

const TooltipContent = React.forwardRef<HTMLDivElement, TooltipContentProps>(
  ({ className, children, side = 'top', sideOffset = 4, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md",
          "absolute",
          side === 'top' && "bottom-full left-1/2 -translate-x-1/2 mb-2",
          side === 'bottom' && "top-full left-1/2 -translate-x-1/2 mt-2",
          side === 'left' && "right-full top-1/2 -translate-y-1/2 mr-2",
          side === 'right' && "left-full top-1/2 -translate-y-1/2 ml-2",
          "opacity-0 peer-data-[tooltip-open=true]:opacity-100",
          "pointer-events-none",
          "hidden group-hover:block",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)
TooltipContent.displayName = 'TooltipContent'

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
