import { redirect } from 'next/navigation'

// Redirect /track to /track/search (or show search interface)
export default function TrackPage() {
  // Show the tracking search page
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 mb-2">Track Your Report</h1>
          <p className="text-slate-400">Enter your ticket number to check status</p>
        </div>

        <form action="/track" method="GET" className="space-y-4">
          <div>
            <label htmlFor="ticket" className="block text-sm font-medium text-slate-300 mb-2">
              Ticket Number
            </label>
            <input
              type="text"
              id="ticket"
              name="ticket"
              placeholder="TKT-XXXXXX"
              required
              minLength={6}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-mono text-lg tracking-wider text-center"
            />
          </div>
          <button
            type="submit"
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors"
          >
            Track Report
          </button>
        </form>

        <div className="mt-8 text-center">
          <a href="/report" className="text-blue-400 hover:text-blue-300 text-sm">
            Submit a new report →
          </a>
        </div>
      </div>
    </div>
  )
}
