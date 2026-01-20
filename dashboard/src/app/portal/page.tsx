'use client'

import { useState } from 'react'
import { 
  Droplets, Search, CreditCard, AlertTriangle, 
  FileText, Phone, MapPin, Clock, CheckCircle,
  ArrowRight, Smartphone, Building, DollarSign
} from 'lucide-react'

export default function CustomerPortalPage() {
  const [accountNumber, setAccountNumber] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [accountData, setAccountData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'lookup' | 'report' | 'pay'>('lookup')

  const handleAccountLookup = async () => {
    if (!accountNumber.trim()) return
    
    setIsSearching(true)
    try {
      // In production, this would fetch from the API
      const response = await fetch(`/api/customer/account?number=${accountNumber}`)
      if (response.ok) {
        const data = await response.json()
        setAccountData(data)
      } else {
        setAccountData(null)
        alert('Account not found. Please check your account number.')
      }
    } catch (error) {
      console.error('Lookup failed:', error)
      alert('Unable to look up account. Please try again.')
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-blue-600 text-white">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Droplets className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">LWSC Customer Portal</h1>
              <p className="text-blue-200 text-sm">Lusaka Water Supply Company</p>
            </div>
          </div>
        </div>
      </header>

      {/* Quick Actions */}
      <div className="max-w-6xl mx-auto px-4 -mt-6">
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <div className="flex flex-wrap gap-4 justify-center">
            <button
              onClick={() => setActiveTab('lookup')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === 'lookup'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Search className="w-5 h-5" />
              Check Balance
            </button>
            <button
              onClick={() => setActiveTab('pay')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === 'pay'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <CreditCard className="w-5 h-5" />
              Pay Bill
            </button>
            <button
              onClick={() => setActiveTab('report')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === 'report'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <AlertTriangle className="w-5 h-5" />
              Report Issue
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {activeTab === 'lookup' && (
          <div className="space-y-6">
            {/* Account Lookup */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-slate-900 mb-4">Account Lookup</h2>
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Enter your account number (e.g., KAB/1/0001/2024)"
                  value={accountNumber}
                  onChange={(e) => setAccountNumber(e.target.value)}
                  className="flex-1 px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleAccountLookup}
                  disabled={isSearching}
                  className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSearching ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>

            {/* Account Details */}
            {accountData ? (
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="bg-blue-600 text-white p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-blue-200 text-sm">Account Number</p>
                      <p className="text-2xl font-bold">{accountData.accountNumber}</p>
                      <p className="text-blue-200 mt-1">{accountData.customerName}</p>
                    </div>
                    <div className={`px-4 py-2 rounded-xl ${
                      accountData.status === 'active' 
                        ? 'bg-green-500/20 text-green-100' 
                        : 'bg-red-500/20 text-red-100'
                    }`}>
                      {accountData.status === 'active' ? 'Active' : 'Disconnected'}
                    </div>
                  </div>
                </div>
                
                <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-50 rounded-xl p-4">
                    <p className="text-slate-500 text-sm">Current Balance</p>
                    <p className="text-3xl font-bold text-slate-900">
                      K{accountData.balance?.toLocaleString() || '0'}
                    </p>
                    {accountData.dueDate && (
                      <p className="text-sm text-slate-500 mt-1">Due: {accountData.dueDate}</p>
                    )}
                  </div>
                  <div className="bg-slate-50 rounded-xl p-4">
                    <p className="text-slate-500 text-sm">Last Payment</p>
                    <p className="text-2xl font-bold text-green-600">
                      K{accountData.lastPayment?.amount?.toLocaleString() || '0'}
                    </p>
                    <p className="text-sm text-slate-500 mt-1">
                      {accountData.lastPayment?.date || 'No payments yet'}
                    </p>
                  </div>
                  <div className="bg-slate-50 rounded-xl p-4">
                    <p className="text-slate-500 text-sm">This Month Usage</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {accountData.currentUsage || 0} m³
                    </p>
                    <p className="text-sm text-slate-500 mt-1">
                      Avg: {accountData.avgUsage || 0} m³/month
                    </p>
                  </div>
                </div>

                {/* Pay Now Button */}
                <div className="p-6 border-t border-slate-100">
                  <button
                    onClick={() => setActiveTab('pay')}
                    className="w-full py-4 bg-green-600 text-white rounded-xl font-bold text-lg hover:bg-green-700 flex items-center justify-center gap-2"
                  >
                    <CreditCard className="w-5 h-5" />
                    Pay K{accountData.balance?.toLocaleString() || '0'} Now
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
                <Search className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-slate-700 mb-2">
                  Enter your account number
                </h3>
                <p className="text-slate-500">
                  Your account number can be found on your water bill or meter installation document.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'pay' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-slate-900 mb-6">Payment Options</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Mobile Money */}
                <div className="border-2 border-slate-200 rounded-xl p-6 hover:border-blue-500 cursor-pointer transition-colors">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                      <Smartphone className="w-6 h-6 text-yellow-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">Mobile Money</h3>
                      <p className="text-sm text-slate-500">MTN, Airtel, Zamtel</p>
                    </div>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">
                    Pay instantly using your mobile money account. Dial *123# or use your mobile money app.
                  </p>
                  <div className="space-y-2 text-sm">
                    <p><strong>MTN:</strong> Dial *123# → Pay Bill → LWSC</p>
                    <p><strong>Airtel:</strong> Dial *778# → Pay Bill → LWSC</p>
                  </div>
                </div>

                {/* Bank Transfer */}
                <div className="border-2 border-slate-200 rounded-xl p-6 hover:border-blue-500 cursor-pointer transition-colors">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                      <Building className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">Bank Transfer</h3>
                      <p className="text-sm text-slate-500">All major banks</p>
                    </div>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">
                    Transfer directly to LWSC bank account.
                  </p>
                  <div className="space-y-1 text-sm bg-slate-50 p-3 rounded-lg">
                    <p><strong>Bank:</strong> Zanaco</p>
                    <p><strong>Account:</strong> 0012345678901</p>
                    <p><strong>Reference:</strong> Your Account Number</p>
                  </div>
                </div>

                {/* Pay at Office */}
                <div className="border-2 border-slate-200 rounded-xl p-6 hover:border-blue-500 cursor-pointer transition-colors">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                      <MapPin className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">Pay at LWSC Office</h3>
                      <p className="text-sm text-slate-500">Cash or card</p>
                    </div>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">
                    Visit any LWSC customer service center.
                  </p>
                  <div className="space-y-1 text-sm">
                    <p><strong>Head Office:</strong> Cairo Road, Lusaka</p>
                    <p><strong>Hours:</strong> Mon-Fri 8:00-17:00</p>
                  </div>
                </div>

                {/* USSD */}
                <div className="border-2 border-slate-200 rounded-xl p-6 hover:border-blue-500 cursor-pointer transition-colors">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                      <Phone className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900">USSD Payment</h3>
                      <p className="text-sm text-slate-500">Dial *789#</p>
                    </div>
                  </div>
                  <p className="text-slate-600 text-sm mb-4">
                    Quick payment via USSD. No internet required.
                  </p>
                  <p className="text-lg font-mono bg-slate-900 text-white px-4 py-2 rounded-lg text-center">
                    *789#
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'report' && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-slate-900 mb-6">Report an Issue</h2>
              
              <form className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Issue Type *
                  </label>
                  <select className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Select issue type</option>
                    <option value="leak">Water Leak</option>
                    <option value="burst">Pipe Burst</option>
                    <option value="no_water">No Water Supply</option>
                    <option value="low_pressure">Low Pressure</option>
                    <option value="dirty_water">Dirty/Discolored Water</option>
                    <option value="meter">Meter Problem</option>
                    <option value="billing">Billing Issue</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Location *
                  </label>
                  <input
                    type="text"
                    placeholder="Enter address or landmark"
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Your Phone Number *
                  </label>
                  <input
                    type="tel"
                    placeholder="+260 9X XXX XXXX"
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Description
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Describe the issue in detail..."
                    className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-4 bg-red-600 text-white rounded-xl font-bold text-lg hover:bg-red-700"
                >
                  Submit Report
                </button>
              </form>
            </div>

            {/* Emergency Contact */}
            <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center">
                  <Phone className="w-7 h-7 text-red-600" />
                </div>
                <div>
                  <h3 className="font-bold text-red-900 text-lg">Emergency Hotline</h3>
                  <p className="text-red-700">For urgent issues, call our 24/7 hotline:</p>
                  <p className="text-2xl font-bold text-red-600 mt-1">+260 211 123 456</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8 mt-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h4 className="font-bold mb-3">Contact Us</h4>
              <p className="text-slate-400 text-sm">Cairo Road, Lusaka</p>
              <p className="text-slate-400 text-sm">+260 211 123 456</p>
              <p className="text-slate-400 text-sm">info@lwsc.com.zm</p>
            </div>
            <div>
              <h4 className="font-bold mb-3">Office Hours</h4>
              <p className="text-slate-400 text-sm">Monday - Friday: 8:00 - 17:00</p>
              <p className="text-slate-400 text-sm">Saturday: 8:00 - 13:00</p>
              <p className="text-slate-400 text-sm">Sunday: Closed</p>
            </div>
            <div>
              <h4 className="font-bold mb-3">Quick Links</h4>
              <p className="text-slate-400 text-sm">Terms & Conditions</p>
              <p className="text-slate-400 text-sm">Privacy Policy</p>
              <p className="text-slate-400 text-sm">FAQ</p>
            </div>
          </div>
          <div className="border-t border-slate-800 mt-8 pt-8 text-center text-slate-500 text-sm">
            © 2026 Lusaka Water Supply Company. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
