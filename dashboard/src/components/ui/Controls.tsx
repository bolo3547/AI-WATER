'use client'

import { clsx } from 'clsx'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  className?: string
  type?: 'button' | 'submit' | 'reset'
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled,
  loading,
  onClick,
  className,
  type = 'button'
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variantStyles = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800',
    secondary: 'bg-surface-secondary text-text-primary border border-surface-border hover:bg-surface-tertiary',
    ghost: 'text-text-secondary hover:text-text-primary hover:bg-surface-secondary',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800'
  }
  
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-caption rounded-md gap-1.5',
    md: 'px-4 py-2 text-body rounded-lg gap-2',
    lg: 'px-6 py-3 text-body rounded-lg gap-2'
  }
  
  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={clsx(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
          <circle 
            className="opacity-25" 
            cx="12" cy="12" r="10" 
            stroke="currentColor" 
            strokeWidth="4" 
            fill="none" 
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" 
          />
        </svg>
      )}
      {children}
    </button>
  )
}

interface TabsProps {
  tabs: { id: string; label: string; count?: number }[]
  activeTab: string
  onChange: (id: string) => void
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 p-1 bg-surface-secondary rounded-lg">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={clsx(
            'px-4 py-2 text-caption font-medium rounded-md transition-colors',
            activeTab === tab.id
              ? 'bg-white text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          )}
        >
          {tab.label}
          {tab.count !== undefined && (
            <span className={clsx(
              'ml-2 px-1.5 py-0.5 rounded text-xs',
              activeTab === tab.id
                ? 'bg-primary-100 text-primary-700'
                : 'bg-surface-tertiary text-text-tertiary'
            )}>
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}

interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function Select({ value, options, onChange, placeholder, className }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={clsx(
        'px-3 py-2 text-body bg-white border border-surface-border rounded-lg',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
        'text-text-primary',
        className
      )}
    >
      {placeholder && (
        <option value="" disabled>{placeholder}</option>
      )}
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}
