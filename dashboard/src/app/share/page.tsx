'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Droplets, ArrowLeft, Printer, Download, Share2, Copy, Check } from 'lucide-react'
import { QRCodeGenerator, QRPoster } from '@/components/QRCodeGenerator'

export default function SharePage() {
  const [copied, setCopied] = useState(false)
  const [showPoster, setShowPoster] = useState(false)

  const reportUrl = typeof window !== 'undefined' 
    ? `${window.location.origin}/report` 
    : 'https://ai-water.vercel.app/report'

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(reportUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const printPoster = () => {
    window.print()
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 sticky top-0 z-40 print:hidden">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/public" className="flex items-center gap-2 text-slate-300 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
            Back
          </Link>
          <div className="flex items-center gap-3">
            <Droplets className="w-6 h-6 text-blue-400" />
            <span className="text-xl font-bold text-white">Share AquaWatch</span>
          </div>
          <div className="w-20"></div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8 print:py-0">
        {/* Info Section */}
        <div className="text-center mb-8 print:hidden">
          <h1 className="text-3xl font-bold text-white mb-3">Share With Your Community</h1>
          <p className="text-slate-400 max-w-lg mx-auto">
            Help spread the word! Share these materials to encourage water leak reporting in your area.
          </p>
        </div>

        {/* Toggle between QR and Poster */}
        <div className="flex justify-center mb-8 print:hidden">
          <div className="bg-slate-800 rounded-lg p-1 flex">
            <button
              onClick={() => setShowPoster(false)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                !showPoster ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              QR Code Only
            </button>
            <button
              onClick={() => setShowPoster(true)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                showPoster ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Printable Poster
            </button>
          </div>
        </div>

        {/* QR Code / Poster Display */}
        <div className="flex justify-center mb-8">
          {showPoster ? (
            <QRPoster url={reportUrl} />
          ) : (
            <QRCodeGenerator url={reportUrl} size={220} showDownload={true} />
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-4 mb-12 print:hidden">
          <button
            onClick={copyLink}
            className="flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors"
          >
            {copied ? <Check className="w-5 h-5 text-emerald-400" /> : <Copy className="w-5 h-5" />}
            {copied ? 'Copied!' : 'Copy Link'}
          </button>

          <button
            onClick={printPoster}
            className="flex items-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors"
          >
            <Printer className="w-5 h-5" />
            Print Poster
          </button>

          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({
                  title: 'Report Water Issues - AquaWatch',
                  text: 'Help report water leaks in your area',
                  url: reportUrl,
                })
              }
            }}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors"
          >
            <Share2 className="w-5 h-5" />
            Share
          </button>
        </div>

        {/* Sharing Ideas */}
        <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6 print:hidden">
          <h2 className="text-xl font-semibold text-white mb-4">💡 Where to Share</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { title: 'Community Notice Boards', desc: 'Post at shopping centers, churches, schools' },
              { title: 'WhatsApp Groups', desc: 'Share in neighborhood and community groups' },
              { title: 'Local Businesses', desc: 'Ask shops to display the poster' },
              { title: 'Social Media', desc: 'Post on Facebook, Twitter, Instagram' },
              { title: 'Water Bills', desc: 'Include QR code with utility bills' },
              { title: 'Public Events', desc: 'Distribute at community meetings' },
            ].map((item, i) => (
              <div key={i} className="flex gap-3 p-3 bg-slate-800/50 rounded-lg">
                <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
                <div>
                  <h4 className="font-medium text-white">{item.title}</h4>
                  <p className="text-sm text-slate-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-8 text-center print:hidden">
          <p className="text-slate-400 mb-4">Direct links for sharing:</p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <code className="px-3 py-1.5 bg-slate-800 rounded-lg text-blue-400">
              {reportUrl}
            </code>
            <code className="px-3 py-1.5 bg-slate-800 rounded-lg text-emerald-400">
              {reportUrl.replace('/report', '/r')}
            </code>
          </div>
        </div>
      </div>

      {/* Print-only styles */}
      <style jsx global>{`
        @media print {
          body {
            background: white !important;
          }
          .print\\:hidden {
            display: none !important;
          }
          .print\\:py-0 {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
          }
        }
      `}</style>
    </div>
  )
}
