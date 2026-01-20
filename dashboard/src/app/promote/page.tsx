'use client'

import { useState } from 'react'
import { 
  QrCode, Copy, Download, ExternalLink, Share2, Printer,
  Smartphone, FileText, Radio, Users, MessageCircle, Check,
  Facebook, Twitter, Mail, Phone, Globe, Megaphone
} from 'lucide-react'

export default function PromotePage() {
  const [copied, setCopied] = useState(false)
  const publicUrl = 'https://ai-iota-blush.vercel.app/report-leak'
  
  const copyToClipboard = () => {
    navigator.clipboard.writeText(publicUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const shareChannels = [
    {
      id: 'whatsapp',
      name: 'WhatsApp',
      icon: MessageCircle,
      color: 'bg-green-500',
      url: `https://wa.me/?text=Report%20water%20leaks%20to%20LWSC%3A%20${encodeURIComponent(publicUrl)}`
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: Facebook,
      color: 'bg-blue-600',
      url: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(publicUrl)}`
    },
    {
      id: 'twitter',
      name: 'Twitter/X',
      icon: Twitter,
      color: 'bg-slate-800',
      url: `https://twitter.com/intent/tweet?text=Report%20water%20leaks%20to%20LWSC&url=${encodeURIComponent(publicUrl)}`
    },
    {
      id: 'email',
      name: 'Email',
      icon: Mail,
      color: 'bg-red-500',
      url: `mailto:?subject=Report%20Leaks%20to%20LWSC&body=Help%20save%20water!%20Report%20leaks%20at%3A%20${encodeURIComponent(publicUrl)}`
    },
  ]

  const promotionIdeas = [
    {
      title: 'Water Bills',
      description: 'Print QR code on every water bill sent to customers',
      icon: FileText,
      impact: 'High'
    },
    {
      title: 'Community Posters',
      description: 'Place posters at markets, bus stops, and community centers',
      icon: Megaphone,
      impact: 'High'
    },
    {
      title: 'Radio Announcements',
      description: 'Broadcast on local radio stations like Phoenix FM, QFM',
      icon: Radio,
      impact: 'Medium'
    },
    {
      title: 'WhatsApp Groups',
      description: 'Share in community, church, and neighborhood groups',
      icon: Users,
      impact: 'High'
    },
    {
      title: 'SMS Campaign',
      description: 'Send bulk SMS to existing LWSC customers',
      icon: Smartphone,
      impact: 'High'
    },
    {
      title: 'Social Media',
      description: 'Post on LWSC Facebook, Twitter, and Instagram pages',
      icon: Globe,
      impact: 'Medium'
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-2 sm:p-4 md:p-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-slate-900">Promote Leak Reporting</h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">Share the public reporting page with the community</p>
          </div>
          <a
            href="/report-leak"
            target="_blank"
            className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-xs sm:text-sm font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            View Public Page
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* QR Code Section */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-slate-100 p-4 sm:p-6">
            <div className="flex items-center gap-2 mb-4">
              <QrCode className="w-5 h-5 text-green-600" />
              <h2 className="text-base sm:text-lg font-semibold text-slate-900">QR Code</h2>
            </div>
            
            {/* QR Code Display */}
            <div className="bg-white border-2 border-dashed border-slate-200 rounded-xl p-4 mb-4">
              <div className="aspect-square bg-white flex items-center justify-center">
                {/* QR Code using Google Charts API */}
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(publicUrl)}&bgcolor=ffffff&color=198038`}
                  alt="QR Code for Leak Reporting"
                  className="w-full max-w-[200px] h-auto"
                />
              </div>
            </div>

            {/* URL Display */}
            <div className="bg-slate-50 rounded-lg p-3 mb-4">
              <p className="text-[10px] text-slate-500 mb-1">Public URL</p>
              <p className="text-xs sm:text-sm text-slate-700 font-mono break-all">{publicUrl}</p>
            </div>

            {/* Actions */}
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={copyToClipboard}
                className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs sm:text-sm font-medium transition-colors ${
                  copied 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied!' : 'Copy URL'}
              </button>
              <a
                href={`https://api.qrserver.com/v1/create-qr-code/?size=500x500&data=${encodeURIComponent(publicUrl)}&bgcolor=ffffff&color=198038&format=png`}
                download="lwsc-leak-report-qr.png"
                className="flex items-center justify-center gap-1.5 py-2 px-3 bg-green-600 text-white rounded-lg text-xs sm:text-sm font-medium hover:bg-green-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </div>
          </div>

          {/* Share Buttons */}
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-slate-100 p-4 sm:p-6 mt-4">
            <div className="flex items-center gap-2 mb-4">
              <Share2 className="w-5 h-5 text-orange-500" />
              <h2 className="text-base sm:text-lg font-semibold text-slate-900">Quick Share</h2>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {shareChannels.map((channel) => (
                <a
                  key={channel.id}
                  href={channel.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-center gap-2 py-2 px-3 ${channel.color} text-white rounded-lg text-xs sm:text-sm font-medium hover:opacity-90 transition-opacity`}
                >
                  <channel.icon className="w-4 h-4" />
                  {channel.name}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Promotion Ideas */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-slate-100 p-4 sm:p-6">
            <div className="flex items-center gap-2 mb-4">
              <Megaphone className="w-5 h-5 text-purple-500" />
              <h2 className="text-base sm:text-lg font-semibold text-slate-900">Promotion Ideas</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {promotionIdeas.map((idea) => (
                <div
                  key={idea.title}
                  className="bg-slate-50 rounded-xl p-4 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                      <idea.icon className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-900">{idea.title}</h3>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                          idea.impact === 'High' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {idea.impact}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{idea.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Print Materials */}
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-slate-100 p-4 sm:p-6 mt-4">
            <div className="flex items-center gap-2 mb-4">
              <Printer className="w-5 h-5 text-blue-500" />
              <h2 className="text-base sm:text-lg font-semibold text-slate-900">Print Materials</h2>
            </div>
            
            {/* Poster Preview */}
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-4 sm:p-6 text-white">
              <div className="text-center">
                <p className="text-[10px] sm:text-xs opacity-80 mb-1">Republic of Zambia</p>
                <h3 className="text-lg sm:text-xl font-bold mb-2">SEE A LEAK?</h3>
                <p className="text-2xl sm:text-3xl font-bold mb-4">REPORT IT!</p>
                
                <div className="bg-white rounded-lg p-3 inline-block mb-4">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(publicUrl)}&bgcolor=ffffff&color=198038`}
                    alt="QR Code"
                    className="w-24 h-24 sm:w-28 sm:h-28"
                  />
                </div>
                
                <p className="text-xs sm:text-sm opacity-90 mb-2">Scan the QR code or visit:</p>
                <p className="text-xs sm:text-sm font-mono bg-white/20 rounded px-2 py-1 inline-block mb-4">
                  {publicUrl.replace('https://', '')}
                </p>
                
                <div className="flex items-center justify-center gap-2 text-orange-200">
                  <Phone className="w-4 h-4" />
                  <span className="text-sm font-medium">Emergency: 211-251778</span>
                </div>
                
                <p className="text-[10px] mt-4 opacity-70">
                  LWSC - Lusaka Water Supply & Sanitation Company
                </p>
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                onClick={() => window.print()}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 text-white rounded-lg text-xs sm:text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                <Printer className="w-4 h-4" />
                Print Poster
              </button>
            </div>
          </div>

          {/* SMS Template */}
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-sm border border-slate-100 p-4 sm:p-6 mt-4">
            <div className="flex items-center gap-2 mb-4">
              <Smartphone className="w-5 h-5 text-cyan-500" />
              <h2 className="text-base sm:text-lg font-semibold text-slate-900">SMS Template</h2>
            </div>
            <div className="bg-slate-50 rounded-lg p-3 mb-3">
              <p className="text-xs sm:text-sm text-slate-700">
                LWSC: See a water leak in your area? Report it instantly at {publicUrl} or call 211-251778. Help us save water! 💧
              </p>
            </div>
            <p className="text-[10px] text-slate-400">Character count: ~140 (fits in 1 SMS)</p>
          </div>
        </div>
      </div>
    </div>
  )
}
