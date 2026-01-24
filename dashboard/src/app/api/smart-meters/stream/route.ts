/**
 * AquaWatch Smart Meters Real-Time Stream
 * =======================================
 * SSE (Server-Sent Events) endpoint for real-time meter data
 * Only streams data when connected to AMI gateway
 */

import { NextRequest } from 'next/server';

// Track connection state (shared with main route)
let streamConnected = false;
let connectionQuality: 'excellent' | 'good' | 'fair' | 'poor' | 'disconnected' = 'disconnected';

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder();
  
  // Check for connection control parameter
  const { searchParams } = new URL(request.url);
  const initialConnect = searchParams.get('connect') === 'true';
  
  if (initialConnect) {
    streamConnected = true;
    connectionQuality = 'excellent';
  }
  
  const stream = new ReadableStream({
    async start(controller) {
      // Send initial connection status
      const sendEvent = (event: string, data: any) => {
        controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));
      };
      
      // Initial connection state
      sendEvent('connection', {
        connected: streamConnected,
        quality: connectionQuality,
        timestamp: new Date().toISOString()
      });
      
      if (!streamConnected) {
        sendEvent('info', {
          message: 'AMI Gateway not connected. Use connect action to start receiving data.',
          action: 'POST /api/smart-meters with { "action": "connect" }'
        });
      }
      
      let counter = 0;
      const interval = setInterval(() => {
        counter++;
        
        // Heartbeat every 30 seconds
        if (counter % 10 === 0) {
          sendEvent('heartbeat', {
            timestamp: new Date().toISOString(),
            uptime: counter * 3
          });
        }
        
        // Only send data if connected
        if (streamConnected) {
          // Simulate connection quality fluctuations
          const qualityRoll = Math.random();
          if (qualityRoll > 0.98) {
            connectionQuality = 'fair';
          } else if (qualityRoll > 0.9) {
            connectionQuality = 'good';
          } else {
            connectionQuality = 'excellent';
          }
          
          // Send random meter updates (simulating real meter transmissions)
          const meterIds = [
            'DMA_IN_CBD', 'DMA_IN_KAB', 'DMA_IN_WOOD', 'DMA_IN_MAT',
            'MTR_R001', 'MTR_R002', 'MTR_R003', 'MTR_R004', 'MTR_R005',
            'MTR_R006', 'MTR_R007', 'MTR_C001', 'MTR_C002', 'MTR_C003',
            'MTR_C004', 'MTR_I001', 'MTR_I002', 'MTR_I003'
          ];
          
          // Pick 1-3 random meters to update
          const metersToUpdate = Math.floor(Math.random() * 3) + 1;
          for (let i = 0; i < metersToUpdate; i++) {
            const meterId = meterIds[Math.floor(Math.random() * meterIds.length)];
            const meterType = meterId.includes('_R') ? 'residential' : 
                              meterId.includes('_C') ? 'commercial' : 
                              meterId.includes('_I') ? 'industrial' : 'dma_inlet';
            
            const baseFlow = meterType === 'residential' ? 30 : 
                             meterType === 'commercial' ? 500 : 
                             meterType === 'industrial' ? 5000 : 3000;
            
            const hour = new Date().getHours();
            const timeFactor = hour >= 6 && hour <= 9 ? 1.5 : 
                               hour >= 18 && hour <= 21 ? 1.3 : 
                               hour >= 0 && hour <= 5 ? 0.2 : 1;
            
            sendEvent('meter_update', {
              meterId,
              flowRate: Math.round(baseFlow * timeFactor * (0.8 + Math.random() * 0.4)),
              signalStrength: Math.round(50 + Math.random() * 50),
              batteryLevel: Math.round(60 + Math.random() * 40),
              timestamp: new Date().toISOString()
            });
          }
          
          // Occasionally send DMA balance updates
          if (counter % 5 === 0) {
            const dmas = ['DMA_CBD', 'DMA_KABULONGA', 'DMA_WOODLANDS', 'DMA_CHILENJE', 'DMA_MATERO'];
            const randomDma = dmas[Math.floor(Math.random() * dmas.length)];
            
            sendEvent('dma_update', {
              dmaId: randomDma,
              nrwPercentage: 15 + Math.random() * 30,
              connectedMeters: Math.floor(Math.random() * 10) + 5,
              timestamp: new Date().toISOString()
            });
          }
          
          // Occasionally generate alerts
          if (Math.random() > 0.95) {
            const alertTypes = ['high_consumption', 'night_flow', 'battery_low', 'signal_lost'];
            const severities = ['low', 'medium', 'high', 'critical'];
            const randomMeter = meterIds[Math.floor(Math.random() * meterIds.length)];
            
            sendEvent('alert', {
              id: `ALT_${Date.now()}`,
              meterId: randomMeter,
              type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
              severity: severities[Math.floor(Math.random() * severities.length)],
              message: 'Automated alert from meter monitoring',
              timestamp: new Date().toISOString()
            });
          }
        } else {
          // Not connected - send periodic disconnected status
          if (counter % 5 === 0) {
            sendEvent('connection', {
              connected: false,
              quality: 'disconnected',
              message: 'Waiting for AMI Gateway connection...',
              timestamp: new Date().toISOString()
            });
          }
        }
        
      }, 3000); // Update every 3 seconds
      
      // Handle disconnect
      request.signal.addEventListener('abort', () => {
        clearInterval(interval);
      });
    }
  });
  
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}

// Allow POST to control connection state
export async function POST(request: NextRequest) {
  const body = await request.json();
  
  if (body.action === 'connect') {
    streamConnected = true;
    connectionQuality = 'excellent';
    return Response.json({ success: true, connected: true });
  }
  
  if (body.action === 'disconnect') {
    streamConnected = false;
    connectionQuality = 'disconnected';
    return Response.json({ success: true, connected: false });
  }
  
  return Response.json({ success: false, error: 'Unknown action' }, { status: 400 });
}
