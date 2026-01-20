'use client';

import React, { useState, useEffect } from 'react';
import { 
  Droplets, CreditCard, FileText, AlertTriangle, Phone, Mail,
  TrendingUp, TrendingDown, Calendar, Clock, CheckCircle, XCircle,
  Download, Bell, User, Home, Settings, LogOut, ChevronRight,
  Smartphone, Banknote, Receipt, History, MessageSquare, Wrench,
  BarChart3, Zap, Shield, HelpCircle, Star, Send
} from 'lucide-react';

interface UsageData {
  month: string;
  usage: number;
  cost: number;
  paid: boolean;
}

interface Bill {
  id: string;
  period: string;
  amount: number;
  dueDate: string;
  status: 'paid' | 'pending' | 'overdue';
  usage: number;
}

interface CustomerReport {
  id: string;
  type: string;
  description: string;
  status: 'open' | 'in-progress' | 'resolved';
  date: string;
  reference: string;
}

export default function CustomerPortalPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'bills' | 'usage' | 'reports' | 'support'>('dashboard');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedBill, setSelectedBill] = useState<Bill | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'mtn' | 'airtel' | 'zamtel' | 'visa'>('mtn');
  
  // Customer data (would come from API)
  const customer = {
    name: 'Mwansa Chisanga',
    accountNumber: 'LWSC-KAB-10234',
    address: 'Plot 123, Kabulonga Road, Lusaka',
    meterNumber: 'ZM-R-10234',
    tariff: 'Residential',
    status: 'Active',
    balance: 245.50,
    lastPayment: '2026-01-05',
    lastReading: 1245.6
  };

  const usageHistory: UsageData[] = [
    { month: 'Jan 2026', usage: 12.5, cost: 106.25, paid: false },
    { month: 'Dec 2025', usage: 14.2, cost: 120.70, paid: true },
    { month: 'Nov 2025', usage: 11.8, cost: 100.30, paid: true },
    { month: 'Oct 2025', usage: 13.5, cost: 114.75, paid: true },
    { month: 'Sep 2025', usage: 15.1, cost: 128.35, paid: true },
    { month: 'Aug 2025', usage: 16.8, cost: 142.80, paid: true },
  ];

  const bills: Bill[] = [
    { id: 'INV-2026-001', period: 'January 2026', amount: 106.25, dueDate: '2026-01-31', status: 'pending', usage: 12.5 },
    { id: 'INV-2025-012', period: 'December 2025', amount: 120.70, dueDate: '2025-12-31', status: 'paid', usage: 14.2 },
    { id: 'INV-2025-011', period: 'November 2025', amount: 100.30, dueDate: '2025-11-30', status: 'paid', usage: 11.8 },
    { id: 'INV-2025-010', period: 'October 2025', amount: 114.75, dueDate: '2025-10-31', status: 'paid', usage: 13.5 },
  ];

  const reports: CustomerReport[] = [
    { id: 'RPT-001', type: 'Leak Report', description: 'Water leaking from main pipe near gate', status: 'in-progress', date: '2026-01-18', reference: 'WO-2847' },
    { id: 'RPT-002', type: 'Low Pressure', description: 'Very low water pressure in the morning', status: 'resolved', date: '2026-01-10', reference: 'WO-2834' },
    { id: 'RPT-003', type: 'Meter Query', description: 'Meter reading seems too high', status: 'resolved', date: '2025-12-15', reference: 'QRY-156' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': case 'resolved': return 'bg-green-100 text-green-700';
      case 'pending': case 'in-progress': return 'bg-amber-100 text-amber-700';
      case 'overdue': case 'open': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-[#198038] to-[#166a2e] text-white">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Droplets className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold">LWSC Customer Portal</h1>
                <p className="text-xs text-white/80">Lusaka Water & Sewerage Company</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-white/10 rounded-lg relative">
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center">2</span>
              </button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4" />
                </div>
                <span className="text-sm hidden md:block">{customer.name}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex gap-1 overflow-x-auto">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: Home },
              { id: 'bills', label: 'Bills & Payments', icon: Receipt },
              { id: 'usage', label: 'Usage History', icon: BarChart3 },
              { id: 'reports', label: 'My Reports', icon: MessageSquare },
              { id: 'support', label: 'Support', icon: HelpCircle },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-[#198038] text-[#198038]'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Account Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-5 border shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-500">Account Balance</span>
                  <CreditCard className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900">K{customer.balance.toFixed(2)}</p>
                <p className="text-xs text-amber-600 mt-1">Due by Jan 31, 2026</p>
                <button 
                  onClick={() => { setSelectedBill(bills[0]); setShowPaymentModal(true); }}
                  className="w-full mt-4 py-2 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e] transition-colors"
                >
                  Pay Now
                </button>
              </div>

              <div className="bg-white rounded-xl p-5 border shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-500">Current Usage</span>
                  <Droplets className="w-5 h-5 text-blue-500" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{usageHistory[0].usage} m³</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="w-4 h-4 text-green-500" />
                  <span className="text-xs text-green-600">12% less than last month</span>
                </div>
                <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: '45%' }} />
                </div>
                <p className="text-xs text-gray-500 mt-1">45% of average monthly usage</p>
              </div>

              <div className="bg-white rounded-xl p-5 border shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-500">Last Meter Reading</span>
                  <Clock className="w-5 h-5 text-gray-400" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{customer.lastReading} m³</p>
                <p className="text-xs text-gray-500 mt-1">Read on Jan 15, 2026</p>
                <div className="flex items-center gap-2 mt-4 p-2 bg-green-50 rounded-lg">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-xs text-green-700">Meter functioning normally</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { icon: AlertTriangle, label: 'Report a Leak', color: 'bg-red-100 text-red-600', action: () => setShowReportModal(true) },
                  { icon: Receipt, label: 'View Bills', color: 'bg-blue-100 text-blue-600', action: () => setActiveTab('bills') },
                  { icon: Download, label: 'Download Statement', color: 'bg-purple-100 text-purple-600', action: () => {} },
                  { icon: Phone, label: 'Call Support', color: 'bg-green-100 text-green-600', action: () => {} },
                ].map((action, i) => (
                  <button
                    key={i}
                    onClick={action.action}
                    className="flex flex-col items-center gap-2 p-4 rounded-xl hover:bg-gray-50 transition-colors border"
                  >
                    <div className={`w-12 h-12 rounded-full ${action.color} flex items-center justify-center`}>
                      <action.icon className="w-6 h-6" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl p-5 border shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Bills</h2>
                <div className="space-y-3">
                  {bills.slice(0, 3).map((bill) => (
                    <div key={bill.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{bill.period}</p>
                        <p className="text-xs text-gray-500">{bill.id}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-gray-900">K{bill.amount.toFixed(2)}</p>
                        <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(bill.status)}`}>
                          {bill.status.charAt(0).toUpperCase() + bill.status.slice(1)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl p-5 border shadow-sm">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">My Reports</h2>
                <div className="space-y-3">
                  {reports.map((report) => (
                    <div key={report.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{report.type}</p>
                        <p className="text-xs text-gray-500">{report.date}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(report.status)}`}>
                        {report.status.replace('-', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Account Info */}
            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: 'Account Number', value: customer.accountNumber },
                  { label: 'Meter Number', value: customer.meterNumber },
                  { label: 'Tariff Category', value: customer.tariff },
                  { label: 'Account Status', value: customer.status, badge: true },
                ].map((item, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">{item.label}</p>
                    {item.badge ? (
                      <span className="inline-block mt-1 px-2 py-0.5 bg-green-100 text-green-700 rounded text-sm font-medium">
                        {item.value}
                      </span>
                    ) : (
                      <p className="text-sm font-medium text-gray-900 mt-1">{item.value}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Bills Tab */}
        {activeTab === 'bills' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Bills & Invoices</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usage</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {bills.map((bill) => (
                      <tr key={bill.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{bill.id}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{bill.period}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{bill.usage} m³</td>
                        <td className="px-4 py-3 text-sm font-bold text-gray-900">K{bill.amount.toFixed(2)}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{bill.dueDate}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded text-xs ${getStatusColor(bill.status)}`}>
                            {bill.status.charAt(0).toUpperCase() + bill.status.slice(1)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {bill.status === 'pending' ? (
                            <button
                              onClick={() => { setSelectedBill(bill); setShowPaymentModal(true); }}
                              className="px-3 py-1 bg-[#198038] text-white rounded text-xs font-medium hover:bg-[#166a2e]"
                            >
                              Pay Now
                            </button>
                          ) : (
                            <button className="px-3 py-1 border border-gray-300 rounded text-xs font-medium hover:bg-gray-50">
                              Download
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Usage Tab */}
        {activeTab === 'usage' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Water Usage History</h2>
              <div className="h-64 flex items-end gap-2">
                {usageHistory.slice().reverse().map((data, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div 
                      className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer"
                      style={{ height: `${(data.usage / 20) * 100}%` }}
                      title={`${data.usage} m³`}
                    />
                    <p className="text-[10px] text-gray-500 mt-2 rotate-45 origin-left">{data.month}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Usage</h2>
              <div className="space-y-3">
                {usageHistory.map((data, i) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <Droplets className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{data.month}</p>
                        <p className="text-sm text-gray-500">Monthly consumption</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900">{data.usage} m³</p>
                      <p className="text-sm text-gray-500">K{data.cost.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">My Reports</h2>
              <button
                onClick={() => setShowReportModal(true)}
                className="px-4 py-2 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]"
              >
                + New Report
              </button>
            </div>
            
            <div className="space-y-4">
              {reports.map((report) => (
                <div key={report.id} className="bg-white rounded-xl p-5 border shadow-sm">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{report.type}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(report.status)}`}>
                          {report.status.replace('-', ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{report.description}</p>
                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                        <span>Ref: {report.reference}</span>
                        <span>Submitted: {report.date}</span>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Support Tab */}
        {activeTab === 'support' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Support</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { icon: Phone, label: 'Call Center', value: '+260 211 252 931', action: 'Call' },
                  { icon: Mail, label: 'Email', value: 'support@lwsc.com.zm', action: 'Email' },
                  { icon: MessageSquare, label: 'WhatsApp', value: '+260 97 123 4567', action: 'Chat' },
                ].map((contact, i) => (
                  <div key={i} className="p-4 bg-gray-50 rounded-xl">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-[#198038]/10 rounded-full flex items-center justify-center">
                        <contact.icon className="w-5 h-5 text-[#198038]" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{contact.label}</p>
                        <p className="text-xs text-gray-500">{contact.value}</p>
                      </div>
                    </div>
                    <button className="w-full py-2 border border-[#198038] text-[#198038] rounded-lg text-sm font-medium hover:bg-[#198038]/5">
                      {contact.action}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl p-5 border shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Frequently Asked Questions</h2>
              <div className="space-y-3">
                {[
                  'How do I read my water meter?',
                  'Why is my bill higher than usual?',
                  'How do I report a water leak?',
                  'What are the payment options available?',
                  'How do I update my contact information?',
                ].map((faq, i) => (
                  <button key={i} className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <span className="text-sm text-gray-700">{faq}</span>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Payment Modal */}
      {showPaymentModal && selectedBill && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Pay Bill</h2>
            
            <div className="p-4 bg-gray-50 rounded-xl mb-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{selectedBill.period}</span>
                <span className="text-xl font-bold text-gray-900">K{selectedBill.amount.toFixed(2)}</span>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Payment Method</label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { id: 'mtn', label: 'MTN MoMo', color: 'bg-yellow-500' },
                  { id: 'airtel', label: 'Airtel Money', color: 'bg-red-500' },
                  { id: 'zamtel', label: 'Zamtel Kwacha', color: 'bg-green-500' },
                  { id: 'visa', label: 'Visa/Mastercard', color: 'bg-blue-500' },
                ].map((method) => (
                  <button
                    key={method.id}
                    onClick={() => setPaymentMethod(method.id as any)}
                    className={`p-3 rounded-xl border-2 transition-colors ${
                      paymentMethod === method.id ? 'border-[#198038] bg-[#198038]/5' : 'border-gray-200'
                    }`}
                  >
                    <div className={`w-8 h-8 ${method.color} rounded-full mb-2 mx-auto`} />
                    <p className="text-xs font-medium text-gray-700">{method.label}</p>
                  </button>
                ))}
              </div>
            </div>

            {paymentMethod !== 'visa' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Mobile Number</label>
                <input
                  type="tel"
                  placeholder="097XXXXXXX"
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#198038]"
                />
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setShowPaymentModal(false)}
                className="flex-1 py-3 border border-gray-300 rounded-xl font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="flex-1 py-3 bg-[#198038] text-white rounded-xl font-medium hover:bg-[#166a2e]">
                Pay K{selectedBill.amount.toFixed(2)}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Report an Issue</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Issue Type</label>
                <select className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#198038]">
                  <option>Water Leak</option>
                  <option>No Water Supply</option>
                  <option>Low Pressure</option>
                  <option>Water Quality</option>
                  <option>Meter Problem</option>
                  <option>Billing Query</option>
                  <option>Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  rows={4}
                  placeholder="Please describe the issue in detail..."
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#198038]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                <input
                  type="text"
                  placeholder="Specific location of the issue"
                  defaultValue={customer.address}
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#198038]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Contact Number</label>
                <input
                  type="tel"
                  placeholder="Your phone number"
                  className="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#198038]"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowReportModal(false)}
                className="flex-1 py-3 border border-gray-300 rounded-xl font-medium hover:bg-gray-50"
              >
                Cancel
              </button>
              <button 
                onClick={() => setShowReportModal(false)}
                className="flex-1 py-3 bg-[#198038] text-white rounded-xl font-medium hover:bg-[#166a2e] flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                Submit Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
