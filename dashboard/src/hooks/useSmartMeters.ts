/**
 * AquaWatch Smart Meters React Hooks
 * ==================================
 * Custom hooks for Smart Meter data with connection awareness
 * Returns null values when not connected - NO FAKE DATA
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  SmartMeter,
  DMABalance,
  SystemStats,
  SystemConnection,
  MeterAlert,
  ConnectionQuality,
  getMeters,
  getDMAs,
  getStats,
  getAlerts,
  connect as apiConnect,
  disconnect as apiDisconnect,
  refreshAllMeters,
  subscribeToMeterStream
} from '@/lib/smart-meters-service';

// ============================================================================
// useSmartMeters Hook - Main hook for meter data
// ============================================================================

export interface UseSmartMetersResult {
  // Connection state
  isConnected: boolean;
  connectionQuality: ConnectionQuality;
  isConnecting: boolean;
  
  // Data (null when disconnected)
  meters: SmartMeter[];
  dmas: DMABalance[];
  stats: SystemStats | null;
  alerts: MeterAlert[];
  
  // Actions
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  refresh: () => Promise<void>;
  
  // Loading/Error states
  isLoading: boolean;
  error: string | null;
  lastUpdate: Date | null;
}

export function useSmartMeters(): UseSmartMetersResult {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState<ConnectionQuality>('disconnected');
  const [isConnecting, setIsConnecting] = useState(false);
  const [meters, setMeters] = useState<SmartMeter[]>([]);
  const [dmas, setDmas] = useState<DMABalance[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [alerts, setAlerts] = useState<MeterAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  
  const unsubscribeRef = useRef<(() => void) | null>(null);
  
  // Load initial data
  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const [metersRes, dmasRes, statsRes, alertsRes] = await Promise.all([
        getMeters(),
        getDMAs(),
        getStats(),
        getAlerts()
      ]);
      
      setIsConnected(metersRes.systemConnected);
      setConnectionQuality(metersRes.connectionQuality || 'disconnected');
      setMeters(metersRes.meters);
      setDmas(dmasRes.dmas);
      setStats(statsRes.stats);
      setAlerts(alertsRes.alerts);
      setLastUpdate(new Date());
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Connect to AMI Gateway
  const connect = useCallback(async () => {
    try {
      setIsConnecting(true);
      setError(null);
      
      const result = await apiConnect();
      
      if (result.success) {
        setIsConnected(true);
        setConnectionQuality('excellent');
        
        // Reload data after connection
        await loadData();
        
        // Start SSE stream for real-time updates
        unsubscribeRef.current = subscribeToMeterStream({
          onConnection: (data) => {
            setIsConnected(data.connected);
            setConnectionQuality(data.quality);
          },
          onMeterUpdate: (data) => {
            setMeters(prev => prev.map(m => 
              m.id === data.meterId 
                ? { ...m, flowRate: data.flowRate, signalStrength: data.signalStrength, batteryLevel: data.batteryLevel, lastUpdate: data.timestamp }
                : m
            ));
            setLastUpdate(new Date());
          },
          onDMAUpdate: (data) => {
            setDmas(prev => prev.map(d =>
              d.id === data.dmaId
                ? { ...d, nrwPercentage: data.nrwPercentage, connectedMeters: data.connectedMeters }
                : d
            ));
          },
          onAlert: (alert) => {
            setAlerts(prev => [alert, ...prev].slice(0, 50));
          },
          onError: (err) => {
            console.error('Stream error:', err);
          }
        });
      } else {
        setError('Failed to connect to AMI Gateway');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
    } finally {
      setIsConnecting(false);
    }
  }, [loadData]);
  
  // Disconnect from AMI Gateway
  const disconnect = useCallback(async () => {
    try {
      // Close SSE stream
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
      
      const result = await apiDisconnect();
      
      if (result.success) {
        setIsConnected(false);
        setConnectionQuality('disconnected');
        
        // Clear live data - meters show as disconnected
        setMeters(prev => prev.map(m => ({
          ...m,
          connected: false,
          status: 'disconnected',
          currentReading: null,
          flowRate: null,
          batteryLevel: null,
          signalStrength: null,
          dailyUsage: null,
          monthlyUsage: null,
          hourlyData: null
        })));
        
        setStats(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Disconnect failed');
    }
  }, []);
  
  // Refresh all data
  const refresh = useCallback(async () => {
    if (!isConnected) {
      setError('Cannot refresh - not connected to AMI Gateway');
      return;
    }
    
    try {
      setIsLoading(true);
      await refreshAllMeters();
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed');
    } finally {
      setIsLoading(false);
    }
  }, [isConnected, loadData]);
  
  // Initial load
  useEffect(() => {
    loadData();
    
    // Cleanup on unmount
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [loadData]);
  
  return {
    isConnected,
    connectionQuality,
    isConnecting,
    meters,
    dmas,
    stats,
    alerts,
    connect,
    disconnect,
    refresh,
    isLoading,
    error,
    lastUpdate
  };
}

// ============================================================================
// useSmartMeterStream Hook - For real-time streaming only
// ============================================================================

export interface UseSmartMeterStreamResult {
  isConnected: boolean;
  connectionQuality: ConnectionQuality;
  lastHeartbeat: Date | null;
  recentUpdates: Array<{
    type: 'meter' | 'dma' | 'alert';
    id: string;
    timestamp: Date;
    data: any;
  }>;
}

export function useSmartMeterStream(): UseSmartMeterStreamResult {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState<ConnectionQuality>('disconnected');
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const [recentUpdates, setRecentUpdates] = useState<UseSmartMeterStreamResult['recentUpdates']>([]);
  
  useEffect(() => {
    const unsubscribe = subscribeToMeterStream({
      onConnection: (data) => {
        setIsConnected(data.connected);
        setConnectionQuality(data.quality);
      },
      onMeterUpdate: (data) => {
        setRecentUpdates(prev => [{
          type: 'meter' as const,
          id: data.meterId,
          timestamp: new Date(data.timestamp),
          data
        }, ...prev].slice(0, 20));
      },
      onDMAUpdate: (data) => {
        setRecentUpdates(prev => [{
          type: 'dma' as const,
          id: data.dmaId,
          timestamp: new Date(data.timestamp),
          data
        }, ...prev].slice(0, 20));
      },
      onAlert: (alert) => {
        setRecentUpdates(prev => [{
          type: 'alert' as const,
          id: alert.id,
          timestamp: new Date(alert.timestamp),
          data: alert
        }, ...prev].slice(0, 20));
      },
      onHeartbeat: (data) => {
        setLastHeartbeat(new Date(data.timestamp));
      }
    });
    
    return () => {
      unsubscribe();
    };
  }, []);
  
  return {
    isConnected,
    connectionQuality,
    lastHeartbeat,
    recentUpdates
  };
}

// ============================================================================
// useMeterDetail Hook - For single meter details
// ============================================================================

export function useMeterDetail(meterId: string | null) {
  const [meter, setMeter] = useState<SmartMeter | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!meterId) {
      setMeter(null);
      return;
    }
    
    const loadMeter = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await fetch(`/api/smart-meters?action=meter&id=${meterId}`);
        const data = await response.json();
        
        if (data.success) {
          setMeter(data.meter);
        } else {
          setError(data.error || 'Failed to load meter');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load meter');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadMeter();
  }, [meterId]);
  
  return { meter, isLoading, error };
}
