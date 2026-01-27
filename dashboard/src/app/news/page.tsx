'use client'

import Link from 'next/link'
import { 
  Droplets, ArrowLeft, Calendar, Clock, ChevronRight,
  AlertTriangle, Wrench, CheckCircle, Megaphone, MapPin
} from 'lucide-react'

interface NewsItem {
  id: string
  title: string
  summary: string
  content: string
  category: 'announcement' | 'maintenance' | 'resolved' | 'alert' | 'update'
  date: string
  location?: string
}

const categoryConfig = {
  'announcement': { label: 'Announcement', color: 'bg-blue-500', icon: Megaphone },
  'maintenance': { label: 'Scheduled Maintenance', color: 'bg-amber-500', icon: Wrench },
  'resolved': { label: 'Issue Resolved', color: 'bg-emerald-500', icon: CheckCircle },
  'alert': { label: 'Service Alert', color: 'bg-red-500', icon: AlertTriangle },
  'update': { label: 'Update', color: 'bg-purple-500', icon: Clock },
}

// Sample news data - in production this would come from an API
const newsItems: NewsItem[] = [
  {
    id: '1',
    title: 'Scheduled Water Supply Interruption - Chilenje Area',
    summary: 'Water supply will be temporarily interrupted for maintenance work on the main pipeline.',
    content: 'Dear valued customers, please be informed that water supply to Chilenje and surrounding areas will be temporarily interrupted on February 1, 2026 from 8:00 AM to 4:00 PM. This is to allow for essential maintenance work on the main distribution pipeline. We advise customers to store sufficient water for use during this period. We apologize for any inconvenience caused.',
    category: 'maintenance',
    date: '2026-01-27T08:00:00Z',
    location: 'Chilenje, Kabulonga, Woodlands'
  },
  {
    id: '2',
    title: 'Major Leak Repaired on Great East Road',
    summary: 'The water leak reported near Arcades Shopping Mall has been successfully repaired.',
    content: 'We are pleased to announce that the major water leak on Great East Road near Arcades Shopping Mall has been successfully repaired. Our field teams worked overnight to fix the burst pipe and restore normal water supply to the affected areas. We thank the community members who reported this issue promptly, which helped us respond quickly and minimize water loss.',
    category: 'resolved',
    date: '2026-01-26T14:30:00Z',
    location: 'Great East Road, Arcades Area'
  },
  {
    id: '3',
    title: 'New Online Reporting System Launched',
    summary: 'Report water issues faster with our new mobile-friendly reporting system.',
    content: 'LWSC is proud to announce the launch of our new online water issue reporting system. Customers can now report leaks, bursts, and other water issues directly through our website or mobile app. The new system includes GPS location tracking, photo uploads, and real-time ticket tracking. This will help us respond to issues faster and reduce water loss across the city.',
    category: 'announcement',
    date: '2026-01-25T10:00:00Z'
  },
  {
    id: '4',
    title: 'Low Pressure Alert - Industrial Area',
    summary: 'Customers in the Industrial Area may experience low water pressure due to high demand.',
    content: 'Due to increased water demand in the Industrial Area, customers may experience lower than normal water pressure during peak hours (6:00 AM - 9:00 AM and 5:00 PM - 8:00 PM). Our teams are working to optimize distribution and improve pressure levels. We recommend storing water during off-peak hours if needed.',
    category: 'alert',
    date: '2026-01-24T16:00:00Z',
    location: 'Industrial Area, Heavy Industrial'
  },
  {
    id: '5',
    title: 'Community Water Conservation Drive',
    summary: 'Join us in our water conservation initiative to reduce water wastage.',
    content: 'LWSC is launching a community water conservation drive starting February 2026. We encourage all customers to report any visible leaks in their neighborhoods, fix dripping taps, and practice water-saving habits. Together, we can reduce Non-Revenue Water and ensure sustainable water supply for everyone. Participants who report valid leaks will receive recognition certificates.',
    category: 'announcement',
    date: '2026-01-23T09:00:00Z'
  },
]

export default function NewsPage() {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-ZM', { 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric'
    })
  }

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return formatDate(dateString)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="bg-slate-950/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back to Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <Droplets className="w-6 h-6 text-blue-400" />
              <span className="font-bold text-white">AquaWatch</span>
            </div>
            <Link href="/report" className="text-blue-400 hover:text-blue-300 text-sm font-medium">
              Report Issue
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="text-center mb-10">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">News & Updates</h1>
          <p className="text-slate-400">Stay informed about water service updates in your area</p>
        </div>

        {/* Featured Alert (if any) */}
        {newsItems.filter(n => n.category === 'alert').length > 0 && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/30 rounded-2xl">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-6 h-6 text-red-400 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-400 mb-1">Active Service Alert</h3>
                <p className="text-slate-300 text-sm">
                  {newsItems.find(n => n.category === 'alert')?.summary}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* News List */}
        <div className="space-y-4">
          {newsItems.map((item) => {
            const CategoryIcon = categoryConfig[item.category].icon
            return (
              <article 
                key={item.id}
                className="bg-slate-800/50 rounded-2xl border border-slate-700 p-6 hover:bg-slate-800/70 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${categoryConfig[item.category].color}/20`}>
                    <CategoryIcon className={`w-6 h-6 ${categoryConfig[item.category].color.replace('bg-', 'text-').replace('500', '400')}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${categoryConfig[item.category].color}`}>
                        {categoryConfig[item.category].label}
                      </span>
                      <span className="text-slate-500 text-xs flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {getTimeAgo(item.date)}
                      </span>
                    </div>
                    <h2 className="text-lg font-semibold text-white mb-2">{item.title}</h2>
                    <p className="text-slate-400 text-sm mb-3">{item.summary}</p>
                    {item.location && (
                      <p className="text-slate-500 text-xs flex items-center gap-1 mb-3">
                        <MapPin className="w-3 h-3" />
                        {item.location}
                      </p>
                    )}
                    <details className="group">
                      <summary className="text-blue-400 text-sm cursor-pointer hover:text-blue-300 flex items-center gap-1">
                        Read more
                        <ChevronRight className="w-4 h-4 group-open:rotate-90 transition-transform" />
                      </summary>
                      <p className="mt-3 text-slate-300 text-sm leading-relaxed border-t border-slate-700 pt-3">
                        {item.content}
                      </p>
                    </details>
                  </div>
                </div>
              </article>
            )
          })}
        </div>

        {/* Load More */}
        <div className="text-center mt-8">
          <button className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors border border-slate-700">
            Load More News
          </button>
        </div>

        {/* Subscribe Section */}
        <div className="mt-12 p-6 bg-blue-500/10 border border-blue-500/30 rounded-2xl text-center">
          <h3 className="text-xl font-semibold text-white mb-2">Stay Updated</h3>
          <p className="text-slate-400 text-sm mb-4">
            Get notified about service updates in your area via SMS or WhatsApp
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center max-w-md mx-auto">
            <input
              type="tel"
              placeholder="Enter phone number"
              className="flex-1 px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
            />
            <button className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors">
              Subscribe
            </button>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-8 grid sm:grid-cols-2 gap-4">
          <Link
            href="/report"
            className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 hover:bg-slate-800 transition-colors flex items-center gap-3"
          >
            <AlertTriangle className="w-6 h-6 text-amber-400" />
            <div>
              <p className="font-medium text-white">Report an Issue</p>
              <p className="text-slate-400 text-sm">Leaks, bursts, or water problems</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-500 ml-auto" />
          </Link>
          <Link
            href="/ticket"
            className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 hover:bg-slate-800 transition-colors flex items-center gap-3"
          >
            <Clock className="w-6 h-6 text-blue-400" />
            <div>
              <p className="font-medium text-white">Track Your Report</p>
              <p className="text-slate-400 text-sm">Check status and chat with us</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-500 ml-auto" />
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-12 py-8">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-slate-500 text-sm">
            © 2026 Lusaka Water & Sewerage Company. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}
