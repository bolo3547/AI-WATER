'use client'

import { useState, useEffect, useCallback, ReactNode } from 'react'
import useSWR, { SWRConfiguration, SWRResponse } from 'swr'
import { AppLoader, LoaderState } from '@/components/loader'

// Global fetcher for SWR
export const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const error = new Error('Failed to fetch data')
    throw error
  }
  return res.json()
}

interface UseDataWithLoaderOptions extends SWRConfiguration {
  loaderState?: LoaderState
  customMessage?: string
  showLoader?: boolean
  minLoadTime?: number
}

/**
 * Custom hook that wraps SWR with the Hippo loading animation
 */
export function useDataWithLoader<T>(
  key: string | null,
  options: UseDataWithLoaderOptions = {}
): SWRResponse<T> & { LoaderComponent: () => ReactNode } {
  const {
    loaderState = 'loading-dashboard',
    customMessage,
    showLoader = true,
    minLoadTime = 800,
    ...swrOptions
  } = options

  const [showLoaderState, setShowLoaderState] = useState(false)
  const [hasInitiallyLoaded, setHasInitiallyLoaded] = useState(false)

  const swr = useSWR<T>(key, fetcher, {
    revalidateOnFocus: false,
    ...swrOptions
  })

  const { isLoading, isValidating, data } = swr

  // Only show loader on initial load, not on revalidation
  useEffect(() => {
    if (isLoading && !hasInitiallyLoaded && showLoader) {
      setShowLoaderState(true)
    }
    if (data && !hasInitiallyLoaded) {
      setHasInitiallyLoaded(true)
      // Small delay before hiding to ensure smooth transition
      setTimeout(() => setShowLoaderState(false), 100)
    }
  }, [isLoading, data, hasInitiallyLoaded, showLoader])

  const LoaderComponent = useCallback(() => {
    if (!showLoader) return null
    return (
      <AppLoader
        isLoading={showLoaderState}
        state={loaderState}
        customMessage={customMessage}
        minDisplayTime={minLoadTime}
        checkLiveStatus={true}
      />
    )
  }, [showLoaderState, loaderState, customMessage, minLoadTime, showLoader])

  return {
    ...swr,
    LoaderComponent
  }
}

/**
 * Provider component that shows loader while fetching initial data
 */
interface DataLoaderProviderProps {
  children: ReactNode
  fetchUrl: string
  loaderState?: LoaderState
  customMessage?: string
  onDataLoaded?: (data: any) => void
}

export function DataLoaderProvider({
  children,
  fetchUrl,
  loaderState = 'loading-dashboard',
  customMessage,
  onDataLoaded
}: DataLoaderProviderProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch(fetchUrl)
        if (!response.ok) throw new Error('Failed to load data')
        const data = await response.json()
        if (onDataLoaded) onDataLoaded(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [fetchUrl, onDataLoaded])

  return (
    <>
      <AppLoader
        isLoading={isLoading}
        state={loaderState}
        customMessage={customMessage}
        checkLiveStatus={true}
      />
      {error ? (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 mb-4">Failed to load: {error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      ) : (
        children
      )}
    </>
  )
}

/**
 * Simple loading wrapper for any async operation
 */
interface LoadingWrapperProps {
  isLoading: boolean
  state?: LoaderState
  message?: string
  children: ReactNode
}

export function LoadingWrapper({
  isLoading,
  state = 'loading-dashboard',
  message,
  children
}: LoadingWrapperProps) {
  return (
    <>
      <AppLoader
        isLoading={isLoading}
        state={state}
        customMessage={message}
        checkLiveStatus={true}
      />
      {children}
    </>
  )
}
