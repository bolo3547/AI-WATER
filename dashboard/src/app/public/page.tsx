'use client'

import { useState } from 'react'
import Link from 'next/link'
import { 
  Droplets, AlertTriangle, MapPin, Phone, MessageCircle, 
  ArrowRight, Shield, Clock, Users, CheckCircle, Smartphone,
  Globe, Zap, Award, ChevronRight, QrCode, ExternalLink
} from 'lucide-react'
import contactConfig from '@/lib/contact-config'

export default function PublicLandingPage() {
  const [showQR, setShowQR] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-xl">
              <Droplets className="w-6 h-6 text-blue-400" />
            </div>
            <span className="text-xl font-bold text-white">AquaWatch</span>
          </div>
          <div className="flex items-center gap-4">
            <Link 
              href="/track" 
              className="text-slate-300 hover:text-white transition-colors hidden sm:block"
            >
              Track Report
            </Link>
            <Link
              href="/report"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
            >
              Report Issue
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-sm mb-8">
            <Shield className="w-4 h-4" />
            Trusted by water utilities across Zambia
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Help Us Stop
            <span className="text-blue-400"> Water Loss</span>
          </h1>
          
          <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Report leaks, bursts, and water issues in your area. Together we can save millions of liters of water every day.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Link
              href="/report"
              className="w-full sm:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold text-lg transition-all hover:scale-105 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25"
            >
              <AlertTriangle className="w-5 h-5" />
              Report Water Issue
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/track"
              className="w-full sm:w-auto px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2 border border-slate-700"
            >
              <MapPin className="w-5 h-5" />
              Track My Report
            </Link>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <p className="text-2xl md:text-3xl font-bold text-blue-400">1,284</p>
              <p className="text-xs md:text-sm text-slate-400">Reports This Month</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <p className="text-2xl md:text-3xl font-bold text-emerald-400">847</p>
              <p className="text-xs md:text-sm text-slate-400">Issues Resolved</p>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <p className="text-2xl md:text-3xl font-bold text-amber-400">4.2h</p>
              <p className="text-xs md:text-sm text-slate-400">Avg Response</p>
            </div>
          </div>
        </div>
      </section>

      {/* How to Report Section */}
      <section className="py-20 px-4 bg-slate-900/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Multiple Ways to Report</h2>
            <p className="text-slate-400">Choose the method that works best for you</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Web */}
            <Link href="/report" className="group p-6 bg-slate-800/50 hover:bg-slate-800 rounded-2xl border border-slate-700 hover:border-blue-500/50 transition-all">
              <div className="p-3 bg-blue-500/20 rounded-xl w-fit mb-4 group-hover:scale-110 transition-transform">
                <Globe className="w-8 h-8 text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Web Portal</h3>
              <p className="text-slate-400 mb-4">
                Use our online form with GPS location and photo upload
              </p>
              <div className="flex items-center gap-2 text-blue-400 font-medium">
                Report Now <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>

            {/* WhatsApp */}
            <a href={contactConfig.whatsapp.url} target="_blank" rel="noopener noreferrer" className="group p-6 bg-slate-800/50 hover:bg-slate-800 rounded-2xl border border-slate-700 hover:border-emerald-500/50 transition-all">
              <div className="p-3 bg-emerald-500/20 rounded-xl w-fit mb-4 group-hover:scale-110 transition-transform">
                <MessageCircle className="w-8 h-8 text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">WhatsApp</h3>
              <p className="text-slate-400 mb-4">
                Chat with our bot to report issues step by step
              </p>
              <div className="flex items-center gap-2 text-emerald-400 font-medium">
                {contactConfig.whatsapp.display} <ExternalLink className="w-4 h-4" />
              </div>
            </a>

            {/* USSD */}
            <div className="group p-6 bg-slate-800/50 hover:bg-slate-800 rounded-2xl border border-slate-700 hover:border-amber-500/50 transition-all">
              <div className="p-3 bg-amber-500/20 rounded-xl w-fit mb-4 group-hover:scale-110 transition-transform">
                <Phone className="w-8 h-8 text-amber-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">USSD</h3>
              <p className="text-slate-400 mb-4">
                Works on any phone, no internet required
              </p>
              <div className="flex items-center gap-2 text-amber-400 font-medium font-mono text-lg">
                {contactConfig.ussd.display}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Issue Types */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">What Can You Report?</h2>
            <p className="text-slate-400">Help us identify and fix water issues in your community</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: '💧', label: 'Leaks', desc: 'Dripping or seeping water' },
              { icon: '💦', label: 'Burst Pipes', desc: 'Major water gushing' },
              { icon: '🚫', label: 'No Water', desc: 'Supply interruption' },
              { icon: '📉', label: 'Low Pressure', desc: 'Weak water flow' },
              { icon: '⚠️', label: 'Illegal Taps', desc: 'Unauthorized connections' },
              { icon: '🌊', label: 'Overflow', desc: 'Tank or reservoir' },
              { icon: '☣️', label: 'Contamination', desc: 'Water quality issues' },
              { icon: '❓', label: 'Other', desc: 'Any water concern' },
            ].map((item, i) => (
              <div key={i} className="p-4 bg-slate-800/30 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors">
                <span className="text-3xl mb-2 block">{item.icon}</span>
                <h4 className="font-semibold text-white">{item.label}</h4>
                <p className="text-sm text-slate-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 bg-slate-900/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">How It Works</h2>
            <p className="text-slate-400">Simple 4-step process to report and track issues</p>
          </div>

          <div className="space-y-6">
            {[
              { step: 1, title: 'Submit Report', desc: 'Describe the issue and share location/photos', icon: Smartphone },
              { step: 2, title: 'Get Ticket', desc: 'Receive a tracking number instantly', icon: QrCode },
              { step: 3, title: 'We Investigate', desc: 'Our team reviews and dispatches technicians', icon: Users },
              { step: 4, title: 'Issue Resolved', desc: 'Track progress until completion', icon: CheckCircle },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4 p-4 bg-slate-800/30 rounded-xl border border-slate-800">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
                  <span className="text-blue-400 font-bold text-lg">{item.step}</span>
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-white text-lg">{item.title}</h4>
                  <p className="text-slate-400">{item.desc}</p>
                </div>
                <item.icon className="w-6 h-6 text-slate-500 hidden sm:block" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* QR Code Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-3xl p-8 md:p-12 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
            <div className="relative">
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                Share With Your Community
              </h2>
              <p className="text-blue-100 mb-8 max-w-lg mx-auto">
                Scan the QR code or share the link to help others report water issues
              </p>

              <button
                onClick={() => setShowQR(!showQR)}
                className="px-6 py-3 bg-white text-blue-600 rounded-xl font-semibold hover:bg-blue-50 transition-colors inline-flex items-center gap-2"
              >
                <QrCode className="w-5 h-5" />
                {showQR ? 'Hide QR Code' : 'Show QR Code'}
              </button>

              {showQR && (
                <div className="mt-8 inline-block p-4 bg-white rounded-2xl">
                  {/* QR Code - using a simple SVG placeholder */}
                  <svg viewBox="0 0 100 100" className="w-48 h-48">
                    <rect fill="white" width="100" height="100"/>
                    <g fill="black">
                      {/* QR pattern - simplified representation */}
                      <rect x="10" y="10" width="20" height="20"/>
                      <rect x="70" y="10" width="20" height="20"/>
                      <rect x="10" y="70" width="20" height="20"/>
                      <rect x="15" y="15" width="10" height="10" fill="white"/>
                      <rect x="75" y="15" width="10" height="10" fill="white"/>
                      <rect x="15" y="75" width="10" height="10" fill="white"/>
                      <rect x="17" y="17" width="6" height="6"/>
                      <rect x="77" y="17" width="6" height="6"/>
                      <rect x="17" y="77" width="6" height="6"/>
                      {/* Data pattern */}
                      <rect x="35" y="10" width="5" height="5"/>
                      <rect x="45" y="10" width="5" height="5"/>
                      <rect x="55" y="10" width="5" height="5"/>
                      <rect x="35" y="20" width="5" height="5"/>
                      <rect x="50" y="20" width="5" height="5"/>
                      <rect x="10" y="35" width="5" height="5"/>
                      <rect x="20" y="35" width="5" height="5"/>
                      <rect x="35" y="35" width="5" height="5"/>
                      <rect x="45" y="35" width="5" height="5"/>
                      <rect x="55" y="35" width="5" height="5"/>
                      <rect x="65" y="35" width="5" height="5"/>
                      <rect x="85" y="35" width="5" height="5"/>
                      <rect x="10" y="45" width="5" height="5"/>
                      <rect x="25" y="45" width="5" height="5"/>
                      <rect x="40" y="45" width="5" height="5"/>
                      <rect x="55" y="45" width="5" height="5"/>
                      <rect x="70" y="45" width="5" height="5"/>
                      <rect x="85" y="45" width="5" height="5"/>
                      <rect x="10" y="55" width="5" height="5"/>
                      <rect x="20" y="55" width="5" height="5"/>
                      <rect x="35" y="55" width="5" height="5"/>
                      <rect x="50" y="55" width="5" height="5"/>
                      <rect x="60" y="55" width="5" height="5"/>
                      <rect x="75" y="55" width="5" height="5"/>
                      <rect x="85" y="55" width="5" height="5"/>
                      <rect x="35" y="70" width="5" height="5"/>
                      <rect x="45" y="70" width="5" height="5"/>
                      <rect x="60" y="70" width="5" height="5"/>
                      <rect x="75" y="70" width="5" height="5"/>
                      <rect x="85" y="70" width="5" height="5"/>
                      <rect x="35" y="80" width="5" height="5"/>
                      <rect x="50" y="80" width="5" height="5"/>
                      <rect x="65" y="80" width="5" height="5"/>
                      <rect x="80" y="80" width="5" height="5"/>
                    </g>
                  </svg>
                  <p className="text-slate-600 text-sm mt-2 font-mono">aquawatch.io/report</p>
                </div>
              )}

              <div className="mt-8 flex flex-wrap justify-center gap-4 text-sm">
                <div className="px-4 py-2 bg-blue-500/30 rounded-full text-white">
                  📱 Works on any smartphone
                </div>
                <div className="px-4 py-2 bg-blue-500/30 rounded-full text-white">
                  🌐 No app download needed
                </div>
                <div className="px-4 py-2 bg-blue-500/30 rounded-full text-white">
                  ⚡ Takes only 2 minutes
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Every Drop Counts
          </h2>
          <p className="text-slate-400 mb-8">
            Your report can save thousands of liters of water and help your community get better service.
          </p>
          <Link
            href="/report"
            className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold text-lg transition-all hover:scale-105 shadow-lg shadow-blue-500/25"
          >
            <AlertTriangle className="w-5 h-5" />
            Report an Issue Now
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Droplets className="w-6 h-6 text-blue-400" />
                <span className="font-bold text-white">AquaWatch</span>
              </div>
              <p className="text-sm text-slate-400">
                AI-powered water loss detection and community reporting platform.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Quick Links</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li><Link href="/report" className="hover:text-white">Report Issue</Link></li>
                <li><Link href="/track" className="hover:text-white">Track Report</Link></li>
                <li><Link href="/r" className="hover:text-white">Quick Report</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Contact</h4>
              <ul className="space-y-2 text-slate-400 text-sm">
                <li>📞 {contactConfig.support.phoneDisplay}</li>
                <li>📱 WhatsApp: {contactConfig.whatsapp.display}</li>
                <li>📧 {contactConfig.support.email}</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Emergency</h4>
              <p className="text-slate-400 text-sm mb-2">
                For burst mains or flooding:
              </p>
              <p className="text-xl font-bold text-red-400">
                📞 {contactConfig.emergency.display}
              </p>
            </div>
          </div>
          <div className="pt-8 border-t border-slate-800 text-center text-slate-500 text-sm">
            <p>© 2026 AquaWatch NRW Detection System. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
