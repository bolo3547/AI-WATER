'use client'

import { useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { Copy, Check, Download, Share2 } from 'lucide-react'
import contactConfig from '@/lib/contact-config'

interface QRCodeGeneratorProps {
  url?: string
  size?: number
  title?: string
  showDownload?: boolean
}

export function QRCodeGenerator({ 
  url = typeof window !== 'undefined' ? `${window.location.origin}/report` : '/report',
  size = 200,
  title = 'Report Water Issues',
  showDownload = true
}: QRCodeGeneratorProps) {
  const [copied, setCopied] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadQR = () => {
    const svg = document.getElementById('qr-code-svg')
    if (!svg) return

    const svgData = new XMLSerializer().serializeToString(svg)
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    canvas.width = size * 2
    canvas.height = size * 2

    img.onload = () => {
      if (ctx) {
        ctx.fillStyle = 'white'
        ctx.fillRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
        
        const pngUrl = canvas.toDataURL('image/png')
        const downloadLink = document.createElement('a')
        downloadLink.href = pngUrl
        downloadLink.download = 'aquawatch-report-qr.png'
        downloadLink.click()
      }
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  const shareQR = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Report Water Issues - AquaWatch',
          text: 'Help report water leaks and issues in your area',
          url: url,
        })
      } catch (err) {
        console.error('Error sharing:', err)
      }
    } else {
      copyToClipboard()
    }
  }

  if (!mounted) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg max-w-xs mx-auto">
      <h3 className="text-lg font-semibold text-slate-800 text-center mb-4">{title}</h3>
      
      <div className="flex justify-center mb-4">
        <QRCodeSVG
          id="qr-code-svg"
          value={url}
          size={size}
          level="H"
          includeMargin={true}
          bgColor="#ffffff"
          fgColor="#1e293b"
        />
      </div>

      <p className="text-center text-sm text-slate-500 mb-4 font-mono break-all">
        {url}
      </p>

      <div className="flex gap-2 justify-center">
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm text-slate-700 transition-colors"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
          {copied ? 'Copied!' : 'Copy'}
        </button>

        {showDownload && (
          <button
            onClick={downloadQR}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm text-slate-700 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download
          </button>
        )}

        <button
          onClick={shareQR}
          className="flex items-center gap-1.5 px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm text-white transition-colors"
        >
          <Share2 className="w-4 h-4" />
          Share
        </button>
      </div>
    </div>
  )
}

// Printable poster component
export function QRPoster({ url }: { url?: string }) {
  const reportUrl = url || (typeof window !== 'undefined' ? `${window.location.origin}/report` : '/report')

  return (
    <div className="bg-white p-8 max-w-md mx-auto print:shadow-none shadow-xl rounded-2xl">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 text-blue-600 mb-2">
          <svg className="w-10 h-10" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <span className="text-2xl font-bold">AquaWatch</span>
        </div>
      </div>

      {/* Main heading */}
      <h1 className="text-3xl font-bold text-center text-slate-800 mb-2">
        🌊 Report Water Leaks
      </h1>
      <p className="text-center text-slate-600 mb-6">
        Help save water in your community
      </p>

      {/* QR Code */}
      <div className="flex justify-center mb-6">
        <div className="p-4 bg-slate-50 rounded-xl border-2 border-dashed border-slate-300">
          <QRCodeSVG
            value={reportUrl}
            size={180}
            level="H"
            includeMargin={true}
          />
        </div>
      </div>

      {/* Instructions */}
      <div className="text-center mb-6">
        <p className="text-lg font-medium text-slate-700 mb-1">
          Scan with your phone camera
        </p>
        <p className="text-sm text-slate-500">
          or visit: <span className="font-mono text-blue-600">{reportUrl.replace('https://', '')}</span>
        </p>
      </div>

      {/* Alternative methods */}
      <div className="border-t border-slate-200 pt-4">
        <p className="text-sm text-slate-600 text-center mb-3">Other ways to report:</p>
        <div className="flex justify-center gap-4 text-sm">
          <div className="text-center">
            <p className="font-medium text-emerald-600">WhatsApp</p>
            <p className="text-slate-500">{contactConfig.whatsapp.display}</p>
          </div>
          <div className="text-center">
            <p className="font-medium text-amber-600">USSD</p>
            <p className="text-slate-500">{contactConfig.ussd.display}</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-slate-200 text-center text-xs text-slate-400">
        Powered by AquaWatch NRW Detection System
      </div>
    </div>
  )
}

export default QRCodeGenerator
