'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  CreditCard, DollarSign, TrendingUp, TrendingDown, Users,
  Search, Filter, Download, Send, AlertTriangle, CheckCircle,
  Clock, Calendar, MoreVertical, Phone, Mail, MapPin, FileText,
  ArrowUpRight, ArrowDownRight, PieChart, BarChart3, RefreshCw
} from 'lucide-react';

type BillingStatus = 'current' | 'overdue' | 'disconnected' | 'pending';
type PaymentMethod = 'mtn-momo' | 'airtel' | 'zamtel' | 'bank' | 'cash';

interface Customer {
  id: string;
  accountNumber: string;
  name: string;
  phone: string;
  email: string;
  address: string;
  dma: string;
  meterNumber: string;
  tariffClass: 'residential' | 'commercial' | 'industrial' | 'institutional';
  status: BillingStatus;
  currentBalance: number;
  lastPayment: { amount: number; date: string; method: PaymentMethod } | null;
  lastReading: { value: number; date: string };
  avgMonthlyUsage: number;
  connectionDate: string;
}

interface Invoice {
  id: string;
  customerId: string;
  customerName: string;
  accountNumber: string;
  period: string;
  dueDate: string;
  consumption: number;
  waterCharge: number;
  sewerCharge: number;
  arrears: number;
  total: number;
  status: 'paid' | 'unpaid' | 'partial' | 'overdue';
  paymentDate: string | null;
}

interface Payment {
  id: string;
  customerId: string;
  customerName: string;
  accountNumber: string;
  amount: number;
  method: PaymentMethod;
  reference: string;
  status: 'completed' | 'pending' | 'failed';
  timestamp: string;
}

// Sample data
const initialCustomers: Customer[] = [
  {
    id: 'CUS-001',
    accountNumber: 'LWSC-2024-00145',
    name: 'Peter Tembo',
    phone: '+260 97 123 4567',
    email: 'peter.tembo@email.com',
    address: 'Plot 45, Leopards Hill Road, Kabulonga',
    dma: 'Kabulonga',
    meterNumber: 'ZM-R-KAB-00123',
    tariffClass: 'residential',
    status: 'current',
    currentBalance: 0,
    lastPayment: { amount: 450, date: '2026-01-15', method: 'mtn-momo' },
    lastReading: { value: 12456, date: '2026-01-18' },
    avgMonthlyUsage: 15.2,
    connectionDate: '2022-03-15'
  },
  {
    id: 'CUS-002',
    accountNumber: 'LWSC-2024-00289',
    name: 'Mwila Trading Ltd',
    phone: '+260 96 555 7890',
    email: 'accounts@mwilatrading.co.zm',
    address: 'Plot 78, Cairo Road, City Centre',
    dma: 'CBD',
    meterNumber: 'ZM-C-CBD-00456',
    tariffClass: 'commercial',
    status: 'overdue',
    currentBalance: 2850,
    lastPayment: { amount: 1500, date: '2025-12-10', method: 'bank' },
    lastReading: { value: 45678, date: '2026-01-17' },
    avgMonthlyUsage: 125.8,
    connectionDate: '2019-08-22'
  },
  {
    id: 'CUS-003',
    accountNumber: 'LWSC-2024-00567',
    name: 'Grace Banda',
    phone: '+260 95 234 5678',
    email: 'grace.banda@gmail.com',
    address: 'House 23, Twin Palm Road, Roma',
    dma: 'Roma',
    meterNumber: 'ZM-R-ROM-00789',
    tariffClass: 'residential',
    status: 'pending',
    currentBalance: 380,
    lastPayment: null,
    lastReading: { value: 8934, date: '2026-01-16' },
    avgMonthlyUsage: 12.5,
    connectionDate: '2025-01-10'
  },
  {
    id: 'CUS-004',
    accountNumber: 'LWSC-2024-00891',
    name: 'University of Zambia',
    phone: '+260 21 129 5000',
    email: 'estates@unza.zm',
    address: 'Great East Road Campus',
    dma: 'UNZA',
    meterNumber: 'ZM-I-UNZ-00001',
    tariffClass: 'institutional',
    status: 'current',
    currentBalance: 0,
    lastPayment: { amount: 45000, date: '2026-01-12', method: 'bank' },
    lastReading: { value: 987654, date: '2026-01-18' },
    avgMonthlyUsage: 2500,
    connectionDate: '1965-07-12'
  },
  {
    id: 'CUS-005',
    accountNumber: 'LWSC-2024-00234',
    name: 'Joseph Mumba',
    phone: '+260 97 987 6543',
    email: 'jmumba@yahoo.com',
    address: 'Plot 12, Matero Main Road',
    dma: 'Matero',
    meterNumber: 'ZM-R-MAT-00567',
    tariffClass: 'residential',
    status: 'disconnected',
    currentBalance: 1250,
    lastPayment: { amount: 200, date: '2025-10-25', method: 'cash' },
    lastReading: { value: 5678, date: '2025-11-15' },
    avgMonthlyUsage: 8.3,
    connectionDate: '2021-05-20'
  },
];

const initialInvoices: Invoice[] = [
  {
    id: 'INV-2026-0145',
    customerId: 'CUS-001',
    customerName: 'Peter Tembo',
    accountNumber: 'LWSC-2024-00145',
    period: 'January 2026',
    dueDate: '2026-02-15',
    consumption: 14.5,
    waterCharge: 362.50,
    sewerCharge: 72.50,
    arrears: 0,
    total: 435,
    status: 'unpaid',
    paymentDate: null
  },
  {
    id: 'INV-2026-0289',
    customerId: 'CUS-002',
    customerName: 'Mwila Trading Ltd',
    accountNumber: 'LWSC-2024-00289',
    period: 'January 2026',
    dueDate: '2026-02-15',
    consumption: 132.4,
    waterCharge: 3310,
    sewerCharge: 662,
    arrears: 2850,
    total: 6822,
    status: 'overdue',
    paymentDate: null
  },
  {
    id: 'INV-2025-0145',
    customerId: 'CUS-001',
    customerName: 'Peter Tembo',
    accountNumber: 'LWSC-2024-00145',
    period: 'December 2025',
    dueDate: '2026-01-15',
    consumption: 15.8,
    waterCharge: 395,
    sewerCharge: 79,
    arrears: 0,
    total: 474,
    status: 'paid',
    paymentDate: '2026-01-15'
  },
];

const initialPayments: Payment[] = [
  {
    id: 'PAY-001',
    customerId: 'CUS-001',
    customerName: 'Peter Tembo',
    accountNumber: 'LWSC-2024-00145',
    amount: 450,
    method: 'mtn-momo',
    reference: 'MTN-789456123',
    status: 'completed',
    timestamp: '2026-01-15T10:30:00'
  },
  {
    id: 'PAY-002',
    customerId: 'CUS-004',
    customerName: 'University of Zambia',
    accountNumber: 'LWSC-2024-00891',
    amount: 45000,
    method: 'bank',
    reference: 'ZNBS-2026-0112',
    status: 'completed',
    timestamp: '2026-01-12T14:22:00'
  },
  {
    id: 'PAY-003',
    customerId: 'CUS-002',
    customerName: 'Mwila Trading Ltd',
    accountNumber: 'LWSC-2024-00289',
    amount: 2000,
    method: 'bank',
    reference: 'ZNBS-2026-0119',
    status: 'pending',
    timestamp: '2026-01-19T09:15:00'
  },
];

// Tariff rates (ZMW per m³)
const tariffRates = {
  residential: { water: 25, sewer: 5 },
  commercial: { water: 25, sewer: 5 },
  industrial: { water: 28, sewer: 5.60 },
  institutional: { water: 22, sewer: 4.40 },
};

export default function BillingPage() {
  const [customers] = useState<Customer[]>(initialCustomers);
  const [invoices] = useState<Invoice[]>(initialInvoices);
  const [payments] = useState<Payment[]>(initialPayments);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [activeTab, setActiveTab] = useState<'customers' | 'invoices' | 'payments' | 'collection'>('customers');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<BillingStatus | 'all'>('all');

  const filteredCustomers = customers
    .filter(c => statusFilter === 'all' || c.status === statusFilter)
    .filter(c => 
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.accountNumber.toLowerCase().includes(searchTerm.toLowerCase())
    );

  const stats = {
    totalCustomers: customers.length,
    totalRevenue: payments.filter(p => p.status === 'completed').reduce((sum, p) => sum + p.amount, 0),
    totalOutstanding: customers.reduce((sum, c) => sum + c.currentBalance, 0),
    overdueAccounts: customers.filter(c => c.status === 'overdue').length,
    disconnected: customers.filter(c => c.status === 'disconnected').length,
    collectionRate: 87.5, // percentage
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-ZM', { 
      style: 'currency', 
      currency: 'ZMW',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const getStatusColor = (status: BillingStatus) => {
    switch (status) {
      case 'current': return 'bg-green-100 text-green-700';
      case 'overdue': return 'bg-red-100 text-red-700';
      case 'disconnected': return 'bg-gray-100 text-gray-700';
      case 'pending': return 'bg-amber-100 text-amber-700';
    }
  };

  const getPaymentMethodLabel = (method: PaymentMethod) => {
    switch (method) {
      case 'mtn-momo': return 'MTN MoMo';
      case 'airtel': return 'Airtel Money';
      case 'zamtel': return 'Zamtel Kwacha';
      case 'bank': return 'Bank Transfer';
      case 'cash': return 'Cash';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 lg:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <CreditCard className="w-7 h-7 text-[#198038]" />
              Billing & Revenue
            </h1>
            <p className="text-sm text-gray-500 mt-1">Customer accounts, invoicing, and payments</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg text-sm font-medium hover:bg-gray-50">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]">
              <FileText className="w-4 h-4" />
              Generate Bills
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500">Customers</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats.totalCustomers.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-500">Revenue (MTD)</span>
          </div>
          <p className="text-lg font-bold text-gray-900">{formatCurrency(stats.totalRevenue)}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-gray-500">Outstanding</span>
          </div>
          <p className="text-lg font-bold text-amber-600">{formatCurrency(stats.totalOutstanding)}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-xs text-gray-500">Overdue</span>
          </div>
          <p className="text-2xl font-bold text-red-600">{stats.overdueAccounts}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-4 h-4 rounded-full bg-gray-400" />
            <span className="text-xs text-gray-500">Disconnected</span>
          </div>
          <p className="text-2xl font-bold text-gray-600">{stats.disconnected}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <PieChart className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-500">Collection Rate</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{stats.collectionRate}%</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4 border-b overflow-x-auto">
        {['customers', 'invoices', 'payments', 'collection'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as typeof activeTab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab 
                ? 'border-[#198038] text-[#198038]' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'customers' ? 'Customer Accounts' : 
             tab === 'invoices' ? 'Invoices' :
             tab === 'payments' ? 'Payments' : 'Debt Collection'}
          </button>
        ))}
      </div>

      {activeTab === 'customers' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Customers List */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by name or account..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038]"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038]"
                >
                  <option value="all">All Status</option>
                  <option value="current">Current</option>
                  <option value="overdue">Overdue</option>
                  <option value="pending">Pending</option>
                  <option value="disconnected">Disconnected</option>
                </select>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-gray-600">Customer</th>
                      <th className="text-left p-4 font-medium text-gray-600">Account</th>
                      <th className="text-left p-4 font-medium text-gray-600">Tariff</th>
                      <th className="text-right p-4 font-medium text-gray-600">Balance</th>
                      <th className="text-center p-4 font-medium text-gray-600">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredCustomers.map((customer) => (
                      <tr 
                        key={customer.id}
                        onClick={() => setSelectedCustomer(customer)}
                        className={`cursor-pointer hover:bg-gray-50 ${selectedCustomer?.id === customer.id ? 'bg-blue-50' : ''}`}
                      >
                        <td className="p-4">
                          <p className="font-medium text-gray-900">{customer.name}</p>
                          <p className="text-xs text-gray-500">{customer.dma}</p>
                        </td>
                        <td className="p-4 font-mono text-xs text-gray-600">{customer.accountNumber}</td>
                        <td className="p-4 capitalize text-gray-600">{customer.tariffClass}</td>
                        <td className="p-4 text-right">
                          <span className={`font-medium ${customer.currentBalance > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {formatCurrency(customer.currentBalance)}
                          </span>
                        </td>
                        <td className="p-4 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(customer.status)}`}>
                            {customer.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Customer Detail */}
          <div className="space-y-4">
            {selectedCustomer ? (
              <>
                <div className="bg-white rounded-xl p-5 shadow-sm border">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-lg font-bold text-gray-900">{selectedCustomer.name}</h2>
                      <p className="text-sm text-gray-500 font-mono">{selectedCustomer.accountNumber}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(selectedCustomer.status)}`}>
                      {selectedCustomer.status}
                    </span>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-900">{selectedCustomer.phone}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-900">{selectedCustomer.email}</span>
                    </div>
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                      <span className="text-gray-900">{selectedCustomer.address}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t">
                    <div>
                      <p className="text-xs text-gray-500">Meter Number</p>
                      <p className="font-mono text-sm">{selectedCustomer.meterNumber}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Tariff Class</p>
                      <p className="text-sm capitalize">{selectedCustomer.tariffClass}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Avg. Monthly Usage</p>
                      <p className="text-sm">{selectedCustomer.avgMonthlyUsage} m³</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Connected Since</p>
                      <p className="text-sm">{selectedCustomer.connectionDate}</p>
                    </div>
                  </div>
                </div>

                {/* Balance Card */}
                <div className={`rounded-xl p-5 border ${
                  selectedCustomer.currentBalance > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
                }`}>
                  <p className="text-sm text-gray-600 mb-1">Current Balance</p>
                  <p className={`text-2xl font-bold ${
                    selectedCustomer.currentBalance > 0 ? 'text-red-700' : 'text-green-700'
                  }`}>
                    {formatCurrency(selectedCustomer.currentBalance)}
                  </p>
                  {selectedCustomer.lastPayment && (
                    <p className="text-xs text-gray-500 mt-2">
                      Last payment: {formatCurrency(selectedCustomer.lastPayment.amount)} on {selectedCustomer.lastPayment.date}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="bg-white rounded-xl p-5 shadow-sm border">
                  <h3 className="font-semibold text-gray-900 mb-3">Quick Actions</h3>
                  <div className="grid grid-cols-2 gap-2">
                    <button className="py-2 px-3 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]">
                      Record Payment
                    </button>
                    <button className="py-2 px-3 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">
                      View Bills
                    </button>
                    <button className="py-2 px-3 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">
                      Send Reminder
                    </button>
                    <button className="py-2 px-3 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">
                      Print Statement
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl p-8 shadow-sm border text-center">
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Select a customer to view details</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'invoices' && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left p-4 font-medium text-gray-600">Invoice</th>
                  <th className="text-left p-4 font-medium text-gray-600">Customer</th>
                  <th className="text-left p-4 font-medium text-gray-600">Period</th>
                  <th className="text-right p-4 font-medium text-gray-600">Consumption</th>
                  <th className="text-right p-4 font-medium text-gray-600">Amount</th>
                  <th className="text-center p-4 font-medium text-gray-600">Status</th>
                  <th className="text-center p-4 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="p-4 font-mono text-xs">{invoice.id}</td>
                    <td className="p-4">
                      <p className="font-medium text-gray-900">{invoice.customerName}</p>
                      <p className="text-xs text-gray-500">{invoice.accountNumber}</p>
                    </td>
                    <td className="p-4 text-gray-600">{invoice.period}</td>
                    <td className="p-4 text-right text-gray-600">{invoice.consumption} m³</td>
                    <td className="p-4 text-right font-medium text-gray-900">{formatCurrency(invoice.total)}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        invoice.status === 'paid' ? 'bg-green-100 text-green-700' :
                        invoice.status === 'overdue' ? 'bg-red-100 text-red-700' :
                        invoice.status === 'partial' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {invoice.status}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <button className="p-1.5 hover:bg-gray-100 rounded">
                        <Download className="w-4 h-4 text-gray-500" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'payments' && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left p-4 font-medium text-gray-600">Reference</th>
                  <th className="text-left p-4 font-medium text-gray-600">Customer</th>
                  <th className="text-left p-4 font-medium text-gray-600">Method</th>
                  <th className="text-right p-4 font-medium text-gray-600">Amount</th>
                  <th className="text-left p-4 font-medium text-gray-600">Date</th>
                  <th className="text-center p-4 font-medium text-gray-600">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {payments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="p-4 font-mono text-xs">{payment.reference}</td>
                    <td className="p-4">
                      <p className="font-medium text-gray-900">{payment.customerName}</p>
                      <p className="text-xs text-gray-500">{payment.accountNumber}</p>
                    </td>
                    <td className="p-4 text-gray-600">{getPaymentMethodLabel(payment.method)}</td>
                    <td className="p-4 text-right font-medium text-green-600">{formatCurrency(payment.amount)}</td>
                    <td className="p-4 text-gray-600">{new Date(payment.timestamp).toLocaleString()}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        payment.status === 'completed' ? 'bg-green-100 text-green-700' :
                        payment.status === 'pending' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {payment.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'collection' && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Debt Aging Report</h2>
            <div className="space-y-3">
              {[
                { label: '0-30 days', amount: 15200, color: 'bg-green-500' },
                { label: '31-60 days', amount: 8500, color: 'bg-amber-500' },
                { label: '61-90 days', amount: 4200, color: 'bg-orange-500' },
                { label: '90+ days', amount: 12600, color: 'bg-red-500' },
              ].map((item, i) => (
                <div key={i}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{item.label}</span>
                    <span className="font-medium text-gray-900">{formatCurrency(item.amount)}</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full">
                    <div className={`h-full ${item.color} rounded-full`} style={{ width: `${(item.amount / 40500) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Top Debtors</h2>
            <div className="space-y-3">
              {customers
                .filter(c => c.currentBalance > 0)
                .sort((a, b) => b.currentBalance - a.currentBalance)
                .slice(0, 5)
                .map((customer, i) => (
                  <div key={customer.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-red-100 text-red-600 text-xs font-medium flex items-center justify-center">
                        {i + 1}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">{customer.name}</p>
                        <p className="text-xs text-gray-500">{customer.accountNumber}</p>
                      </div>
                    </div>
                    <span className="font-semibold text-red-600">{formatCurrency(customer.currentBalance)}</span>
                  </div>
                ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Collection Actions</h2>
            <div className="space-y-2">
              <button className="w-full py-3 px-4 bg-amber-100 text-amber-700 rounded-lg text-sm font-medium hover:bg-amber-200 flex items-center gap-2 justify-center">
                <Send className="w-4 h-4" />
                Send Bulk Reminders (15 accounts)
              </button>
              <button className="w-full py-3 px-4 bg-orange-100 text-orange-700 rounded-lg text-sm font-medium hover:bg-orange-200 flex items-center gap-2 justify-center">
                <AlertTriangle className="w-4 h-4" />
                Issue Disconnection Notices (8 accounts)
              </button>
              <button className="w-full py-3 px-4 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 flex items-center gap-2 justify-center">
                <Clock className="w-4 h-4" />
                Schedule Disconnections (3 accounts)
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Payment Methods Distribution</h2>
            <div className="space-y-2">
              {[
                { method: 'MTN MoMo', percentage: 45, color: 'bg-yellow-500' },
                { method: 'Bank Transfer', percentage: 30, color: 'bg-blue-500' },
                { method: 'Airtel Money', percentage: 15, color: 'bg-red-500' },
                { method: 'Cash', percentage: 7, color: 'bg-green-500' },
                { method: 'Zamtel Kwacha', percentage: 3, color: 'bg-purple-500' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${item.color}`} />
                  <span className="text-sm text-gray-700 flex-1">{item.method}</span>
                  <span className="text-sm font-medium text-gray-900">{item.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
