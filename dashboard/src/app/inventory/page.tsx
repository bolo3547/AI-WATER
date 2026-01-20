'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Package, AlertTriangle, TrendingUp, TrendingDown, Search,
  Plus, Minus, Filter, Download, ShoppingCart, Truck, Warehouse,
  CheckCircle, XCircle, Clock, Edit, MoreVertical, RefreshCw,
  BarChart3, Box, Wrench, ArrowUpDown, ChevronRight
} from 'lucide-react';

type ItemCategory = 'pipes' | 'fittings' | 'meters' | 'valves' | 'chemicals' | 'tools' | 'electrical';
type StockStatus = 'in-stock' | 'low-stock' | 'out-of-stock' | 'on-order';

interface InventoryItem {
  id: string;
  name: string;
  sku: string;
  category: ItemCategory;
  description: string;
  unit: string;
  quantity: number;
  minStock: number;
  maxStock: number;
  reorderPoint: number;
  unitCost: number; // ZMW
  location: string;
  supplier: string;
  lastRestocked: string;
  status: StockStatus;
}

interface Transaction {
  id: string;
  itemId: string;
  itemName: string;
  type: 'issue' | 'receive' | 'return' | 'adjust';
  quantity: number;
  workOrderId: string | null;
  performedBy: string;
  timestamp: string;
  notes: string;
}

interface PurchaseOrder {
  id: string;
  items: { itemId: string; itemName: string; quantity: number; unitCost: number }[];
  supplier: string;
  status: 'pending' | 'approved' | 'ordered' | 'shipped' | 'received';
  createdAt: string;
  expectedDelivery: string | null;
  total: number;
}

// Sample inventory data
const initialInventory: InventoryItem[] = [
  {
    id: 'INV-001',
    name: 'HDPE Pipe 110mm',
    sku: 'PIPE-HDPE-110',
    category: 'pipes',
    description: 'High-density polyethylene pipe, 110mm diameter, PN10',
    unit: 'meters',
    quantity: 450,
    minStock: 100,
    maxStock: 1000,
    reorderPoint: 200,
    unitCost: 85,
    location: 'Warehouse A - Row 1',
    supplier: 'Pipes & Fittings Zambia Ltd',
    lastRestocked: '2026-01-10',
    status: 'in-stock'
  },
  {
    id: 'INV-002',
    name: 'PVC Pipe 50mm',
    sku: 'PIPE-PVC-50',
    category: 'pipes',
    description: 'PVC pressure pipe, 50mm diameter, Class D',
    unit: 'meters',
    quantity: 320,
    minStock: 150,
    maxStock: 800,
    reorderPoint: 250,
    unitCost: 35,
    location: 'Warehouse A - Row 2',
    supplier: 'Pipes & Fittings Zambia Ltd',
    lastRestocked: '2026-01-15',
    status: 'in-stock'
  },
  {
    id: 'INV-003',
    name: 'Electrofusion Coupler 110mm',
    sku: 'FIT-EF-110',
    category: 'fittings',
    description: 'Electrofusion coupling for HDPE pipes, 110mm',
    unit: 'pieces',
    quantity: 45,
    minStock: 30,
    maxStock: 150,
    reorderPoint: 50,
    unitCost: 280,
    location: 'Warehouse B - Shelf 3',
    supplier: 'Georg Fischer Zambia',
    lastRestocked: '2026-01-08',
    status: 'low-stock'
  },
  {
    id: 'INV-004',
    name: 'Smart Water Meter ZM-R',
    sku: 'MTR-ZMR-15',
    category: 'meters',
    description: 'Smart meter with NB-IoT, 15mm residential',
    unit: 'pieces',
    quantity: 125,
    minStock: 50,
    maxStock: 300,
    reorderPoint: 75,
    unitCost: 1200,
    location: 'Warehouse B - Secured',
    supplier: 'Kamstrup Zambia',
    lastRestocked: '2026-01-12',
    status: 'in-stock'
  },
  {
    id: 'INV-005',
    name: 'Gate Valve 150mm',
    sku: 'VLV-GATE-150',
    category: 'valves',
    description: 'Cast iron gate valve, 150mm, PN16',
    unit: 'pieces',
    quantity: 8,
    minStock: 10,
    maxStock: 40,
    reorderPoint: 15,
    unitCost: 4500,
    location: 'Warehouse A - Heavy',
    supplier: 'AVK Zambia',
    lastRestocked: '2025-12-20',
    status: 'low-stock'
  },
  {
    id: 'INV-006',
    name: 'Chlorine Tablets 65%',
    sku: 'CHEM-CL-65',
    category: 'chemicals',
    description: 'Calcium hypochlorite tablets, 65% available chlorine',
    unit: 'kg',
    quantity: 180,
    minStock: 100,
    maxStock: 500,
    reorderPoint: 150,
    unitCost: 95,
    location: 'Chemical Store',
    supplier: 'Water Chem Solutions',
    lastRestocked: '2026-01-05',
    status: 'in-stock'
  },
  {
    id: 'INV-007',
    name: 'Repair Clamp 110mm',
    sku: 'FIT-RC-110',
    category: 'fittings',
    description: 'Stainless steel repair clamp for emergency repairs',
    unit: 'pieces',
    quantity: 0,
    minStock: 20,
    maxStock: 80,
    reorderPoint: 30,
    unitCost: 350,
    location: 'Warehouse B - Shelf 2',
    supplier: 'Pipes & Fittings Zambia Ltd',
    lastRestocked: '2025-12-15',
    status: 'out-of-stock'
  },
  {
    id: 'INV-008',
    name: 'PRV 80mm',
    sku: 'VLV-PRV-80',
    category: 'valves',
    description: 'Pressure reducing valve, 80mm, adjustable 1-10 bar',
    unit: 'pieces',
    quantity: 12,
    minStock: 5,
    maxStock: 25,
    reorderPoint: 8,
    unitCost: 8500,
    location: 'Warehouse A - Heavy',
    supplier: 'Bermad Zambia',
    lastRestocked: '2026-01-02',
    status: 'in-stock'
  },
  {
    id: 'INV-009',
    name: 'Acoustic Leak Detector',
    sku: 'TOOL-ALD-1',
    category: 'tools',
    description: 'Digital acoustic leak detection equipment',
    unit: 'pieces',
    quantity: 4,
    minStock: 2,
    maxStock: 8,
    reorderPoint: 3,
    unitCost: 25000,
    location: 'Equipment Room',
    supplier: 'SebaKMT',
    lastRestocked: '2025-11-01',
    status: 'in-stock'
  },
  {
    id: 'INV-010',
    name: 'Meter Box Concrete',
    sku: 'MTR-BOX-CON',
    category: 'meters',
    description: 'Pre-cast concrete meter box with lid',
    unit: 'pieces',
    quantity: 65,
    minStock: 40,
    maxStock: 200,
    reorderPoint: 60,
    unitCost: 180,
    location: 'Outdoor Yard',
    supplier: 'Lafarge Zambia',
    lastRestocked: '2026-01-14',
    status: 'in-stock'
  },
];

const initialTransactions: Transaction[] = [
  {
    id: 'TXN-001',
    itemId: 'INV-001',
    itemName: 'HDPE Pipe 110mm',
    type: 'issue',
    quantity: 25,
    workOrderId: 'WO-2847',
    performedBy: 'John Mwale',
    timestamp: '2026-01-18T09:30:00',
    notes: 'Issued for Matero leak repair'
  },
  {
    id: 'TXN-002',
    itemId: 'INV-003',
    itemName: 'Electrofusion Coupler 110mm',
    type: 'issue',
    quantity: 3,
    workOrderId: 'WO-2847',
    performedBy: 'John Mwale',
    timestamp: '2026-01-18T09:35:00',
    notes: 'Issued for Matero leak repair'
  },
  {
    id: 'TXN-003',
    itemId: 'INV-004',
    itemName: 'Smart Water Meter ZM-R',
    type: 'issue',
    quantity: 5,
    workOrderId: 'WO-2848',
    performedBy: 'Grace Banda',
    timestamp: '2026-01-19T08:00:00',
    notes: 'Meter installations Kabulonga'
  },
  {
    id: 'TXN-004',
    itemId: 'INV-006',
    itemName: 'Chlorine Tablets 65%',
    type: 'receive',
    quantity: 100,
    workOrderId: null,
    performedBy: 'Stores Manager',
    timestamp: '2026-01-17T14:00:00',
    notes: 'PO-2341 delivery from Water Chem'
  },
];

const initialPurchaseOrders: PurchaseOrder[] = [
  {
    id: 'PO-2345',
    items: [
      { itemId: 'INV-007', itemName: 'Repair Clamp 110mm', quantity: 50, unitCost: 350 },
      { itemId: 'INV-003', itemName: 'Electrofusion Coupler 110mm', quantity: 30, unitCost: 280 },
    ],
    supplier: 'Pipes & Fittings Zambia Ltd',
    status: 'ordered',
    createdAt: '2026-01-16',
    expectedDelivery: '2026-01-22',
    total: 25900
  },
  {
    id: 'PO-2346',
    items: [
      { itemId: 'INV-005', itemName: 'Gate Valve 150mm', quantity: 10, unitCost: 4500 },
    ],
    supplier: 'AVK Zambia',
    status: 'approved',
    createdAt: '2026-01-18',
    expectedDelivery: null,
    total: 45000
  },
];

export default function InventoryPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>(initialInventory);
  const [transactions] = useState<Transaction[]>(initialTransactions);
  const [purchaseOrders] = useState<PurchaseOrder[]>(initialPurchaseOrders);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<ItemCategory | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<StockStatus | 'all'>('all');
  const [showIssueModal, setShowIssueModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'inventory' | 'transactions' | 'orders'>('inventory');

  const filteredInventory = inventory
    .filter(item => categoryFilter === 'all' || item.category === categoryFilter)
    .filter(item => statusFilter === 'all' || item.status === statusFilter)
    .filter(item => 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.sku.toLowerCase().includes(searchTerm.toLowerCase())
    );

  const stats = {
    totalItems: inventory.length,
    totalValue: inventory.reduce((sum, item) => sum + (item.quantity * item.unitCost), 0),
    lowStock: inventory.filter(i => i.status === 'low-stock').length,
    outOfStock: inventory.filter(i => i.status === 'out-of-stock').length,
    pendingOrders: purchaseOrders.filter(po => po.status !== 'received').length,
  };

  const getStatusColor = (status: StockStatus) => {
    switch (status) {
      case 'in-stock': return 'bg-green-100 text-green-700';
      case 'low-stock': return 'bg-amber-100 text-amber-700';
      case 'out-of-stock': return 'bg-red-100 text-red-700';
      case 'on-order': return 'bg-blue-100 text-blue-700';
    }
  };

  const getCategoryIcon = (category: ItemCategory) => {
    switch (category) {
      case 'pipes': return Box;
      case 'fittings': return Package;
      case 'meters': return BarChart3;
      case 'valves': return Wrench;
      case 'chemicals': return Package;
      case 'tools': return Wrench;
      case 'electrical': return Package;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-ZM', { 
      style: 'currency', 
      currency: 'ZMW',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 lg:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Warehouse className="w-7 h-7 text-[#198038]" />
              Inventory Management
            </h1>
            <p className="text-sm text-gray-500 mt-1">Track materials, equipment, and supplies</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg text-sm font-medium hover:bg-gray-50">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]">
              <Plus className="w-4 h-4" />
              Add Item
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <Package className="w-4 h-4 text-gray-400" />
            <span className="text-xs text-gray-500">Total Items</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats.totalItems}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-500">Total Value</span>
          </div>
          <p className="text-lg font-bold text-gray-900">{formatCurrency(stats.totalValue)}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-gray-500">Low Stock</span>
          </div>
          <p className="text-2xl font-bold text-amber-600">{stats.lowStock}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-xs text-gray-500">Out of Stock</span>
          </div>
          <p className="text-2xl font-bold text-red-600">{stats.outOfStock}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <Truck className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-500">Pending Orders</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{stats.pendingOrders}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4 border-b">
        {['inventory', 'transactions', 'orders'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as typeof activeTab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab 
                ? 'border-[#198038] text-[#198038]' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'inventory' ? 'Stock Items' : tab === 'transactions' ? 'Transactions' : 'Purchase Orders'}
          </button>
        ))}
      </div>

      {activeTab === 'inventory' && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Inventory List */}
          <div className="lg:col-span-2 space-y-4">
            {/* Filters */}
            <div className="bg-white rounded-xl p-4 shadow-sm border">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by name or SKU..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038]"
                  />
                </div>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value as any)}
                  className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038]"
                >
                  <option value="all">All Categories</option>
                  <option value="pipes">Pipes</option>
                  <option value="fittings">Fittings</option>
                  <option value="meters">Meters</option>
                  <option value="valves">Valves</option>
                  <option value="chemicals">Chemicals</option>
                  <option value="tools">Tools</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038]"
                >
                  <option value="all">All Status</option>
                  <option value="in-stock">In Stock</option>
                  <option value="low-stock">Low Stock</option>
                  <option value="out-of-stock">Out of Stock</option>
                </select>
              </div>
            </div>

            {/* Items Table */}
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-gray-600">Item</th>
                      <th className="text-left p-4 font-medium text-gray-600">SKU</th>
                      <th className="text-right p-4 font-medium text-gray-600">Qty</th>
                      <th className="text-right p-4 font-medium text-gray-600">Unit Cost</th>
                      <th className="text-center p-4 font-medium text-gray-600">Status</th>
                      <th className="text-center p-4 font-medium text-gray-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredInventory.map((item) => {
                      const Icon = getCategoryIcon(item.category);
                      return (
                        <tr 
                          key={item.id} 
                          onClick={() => setSelectedItem(item)}
                          className={`cursor-pointer hover:bg-gray-50 ${selectedItem?.id === item.id ? 'bg-blue-50' : ''}`}
                        >
                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 rounded flex items-center justify-center ${
                                item.status === 'out-of-stock' ? 'bg-red-100' :
                                item.status === 'low-stock' ? 'bg-amber-100' : 'bg-gray-100'
                              }`}>
                                <Icon className="w-4 h-4 text-gray-600" />
                              </div>
                              <div>
                                <p className="font-medium text-gray-900">{item.name}</p>
                                <p className="text-xs text-gray-500">{item.location}</p>
                              </div>
                            </div>
                          </td>
                          <td className="p-4 text-gray-600 font-mono text-xs">{item.sku}</td>
                          <td className="p-4 text-right">
                            <span className={`font-semibold ${
                              item.quantity <= item.minStock ? 'text-red-600' : 'text-gray-900'
                            }`}>
                              {item.quantity}
                            </span>
                            <span className="text-gray-400 text-xs ml-1">{item.unit}</span>
                          </td>
                          <td className="p-4 text-right text-gray-600">{formatCurrency(item.unitCost)}</td>
                          <td className="p-4 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(item.status)}`}>
                              {item.status.replace('-', ' ')}
                            </span>
                          </td>
                          <td className="p-4 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <button 
                                onClick={(e) => { e.stopPropagation(); setShowIssueModal(true); }}
                                className="p-1.5 hover:bg-gray-100 rounded"
                                title="Issue"
                              >
                                <Minus className="w-4 h-4 text-gray-500" />
                              </button>
                              <button 
                                onClick={(e) => e.stopPropagation()}
                                className="p-1.5 hover:bg-gray-100 rounded"
                                title="Receive"
                              >
                                <Plus className="w-4 h-4 text-gray-500" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Detail Panel */}
          <div className="space-y-4">
            {selectedItem ? (
              <>
                <div className="bg-white rounded-xl p-5 shadow-sm border">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-lg font-bold text-gray-900">{selectedItem.name}</h2>
                      <p className="text-sm text-gray-500 font-mono">{selectedItem.sku}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(selectedItem.status)}`}>
                      {selectedItem.status.replace('-', ' ')}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-4">{selectedItem.description}</p>

                  {/* Stock Level Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-500">Stock Level</span>
                      <span className="text-gray-700">{selectedItem.quantity} / {selectedItem.maxStock} {selectedItem.unit}</span>
                    </div>
                    <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${
                          selectedItem.quantity <= selectedItem.minStock ? 'bg-red-500' :
                          selectedItem.quantity <= selectedItem.reorderPoint ? 'bg-amber-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(100, (selectedItem.quantity / selectedItem.maxStock) * 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs mt-1 text-gray-400">
                      <span>Min: {selectedItem.minStock}</span>
                      <span>Reorder: {selectedItem.reorderPoint}</span>
                      <span>Max: {selectedItem.maxStock}</span>
                    </div>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Category</span>
                      <span className="text-gray-900 capitalize">{selectedItem.category}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Unit Cost</span>
                      <span className="text-gray-900">{formatCurrency(selectedItem.unitCost)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Total Value</span>
                      <span className="text-gray-900 font-semibold">{formatCurrency(selectedItem.quantity * selectedItem.unitCost)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Location</span>
                      <span className="text-gray-900">{selectedItem.location}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Supplier</span>
                      <span className="text-gray-900">{selectedItem.supplier}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Last Restocked</span>
                      <span className="text-gray-900">{selectedItem.lastRestocked}</span>
                    </div>
                  </div>

                  <div className="flex gap-2 mt-5">
                    <button 
                      onClick={() => setShowIssueModal(true)}
                      className="flex-1 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50"
                    >
                      Issue Stock
                    </button>
                    <button className="flex-1 py-2 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]">
                      Receive Stock
                    </button>
                  </div>
                </div>

                {/* Recent Transactions for Item */}
                <div className="bg-white rounded-xl p-5 shadow-sm border">
                  <h3 className="font-semibold text-gray-900 mb-3">Recent Activity</h3>
                  <div className="space-y-2">
                    {transactions.filter(t => t.itemId === selectedItem.id).slice(0, 5).map((txn) => (
                      <div key={txn.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <div className={`w-6 h-6 rounded flex items-center justify-center ${
                            txn.type === 'issue' ? 'bg-red-100' : 'bg-green-100'
                          }`}>
                            {txn.type === 'issue' ? <Minus className="w-3 h-3 text-red-600" /> : <Plus className="w-3 h-3 text-green-600" />}
                          </div>
                          <div>
                            <p className="text-xs font-medium text-gray-900">{txn.type === 'issue' ? 'Issued' : 'Received'}</p>
                            <p className="text-xs text-gray-500">{txn.performedBy}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-medium ${txn.type === 'issue' ? 'text-red-600' : 'text-green-600'}`}>
                            {txn.type === 'issue' ? '-' : '+'}{txn.quantity}
                          </p>
                          <p className="text-xs text-gray-400">{new Date(txn.timestamp).toLocaleDateString()}</p>
                        </div>
                      </div>
                    ))}
                    {transactions.filter(t => t.itemId === selectedItem.id).length === 0 && (
                      <p className="text-sm text-gray-500 text-center py-2">No recent activity</p>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl p-8 shadow-sm border text-center">
                <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">Select an item to view details</p>
              </div>
            )}

            {/* Low Stock Alert */}
            <div className="bg-amber-50 rounded-xl p-5 border border-amber-200">
              <h3 className="font-semibold text-amber-800 flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4" />
                Reorder Required
              </h3>
              <div className="space-y-2">
                {inventory.filter(i => i.status === 'low-stock' || i.status === 'out-of-stock').map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-2 bg-white rounded-lg">
                    <span className="text-sm text-gray-700">{item.name}</span>
                    <span className={`text-xs font-medium ${item.status === 'out-of-stock' ? 'text-red-600' : 'text-amber-600'}`}>
                      {item.quantity} left
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'transactions' && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left p-4 font-medium text-gray-600">ID</th>
                  <th className="text-left p-4 font-medium text-gray-600">Item</th>
                  <th className="text-left p-4 font-medium text-gray-600">Type</th>
                  <th className="text-right p-4 font-medium text-gray-600">Qty</th>
                  <th className="text-left p-4 font-medium text-gray-600">Work Order</th>
                  <th className="text-left p-4 font-medium text-gray-600">By</th>
                  <th className="text-left p-4 font-medium text-gray-600">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {transactions.map((txn) => (
                  <tr key={txn.id} className="hover:bg-gray-50">
                    <td className="p-4 font-mono text-xs text-gray-500">{txn.id}</td>
                    <td className="p-4 font-medium text-gray-900">{txn.itemName}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        txn.type === 'issue' ? 'bg-red-100 text-red-700' :
                        txn.type === 'receive' ? 'bg-green-100 text-green-700' :
                        txn.type === 'return' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {txn.type}
                      </span>
                    </td>
                    <td className={`p-4 text-right font-medium ${
                      txn.type === 'issue' ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {txn.type === 'issue' ? '-' : '+'}{txn.quantity}
                    </td>
                    <td className="p-4 text-gray-600">{txn.workOrderId || '-'}</td>
                    <td className="p-4 text-gray-600">{txn.performedBy}</td>
                    <td className="p-4 text-gray-600">{new Date(txn.timestamp).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'orders' && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-900">Purchase Orders</h2>
            <button className="flex items-center gap-2 px-3 py-1.5 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]">
              <Plus className="w-4 h-4" />
              New Order
            </button>
          </div>
          <div className="divide-y">
            {purchaseOrders.map((po) => (
              <div key={po.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="font-mono text-sm font-medium text-gray-900">{po.id}</span>
                    <p className="text-sm text-gray-500">{po.supplier}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    po.status === 'pending' ? 'bg-gray-100 text-gray-700' :
                    po.status === 'approved' ? 'bg-blue-100 text-blue-700' :
                    po.status === 'ordered' ? 'bg-purple-100 text-purple-700' :
                    po.status === 'shipped' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {po.status}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  {po.items.map(item => `${item.quantity}x ${item.itemName}`).join(', ')}
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">
                    Created: {po.createdAt}
                    {po.expectedDelivery && ` • Expected: ${po.expectedDelivery}`}
                  </span>
                  <span className="font-semibold text-gray-900">{formatCurrency(po.total)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issue Modal */}
      {showIssueModal && selectedItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Issue Stock</h2>
            <p className="text-sm text-gray-600 mb-4">{selectedItem.name}</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input 
                  type="number" 
                  defaultValue={1}
                  min={1}
                  max={selectedItem.quantity}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" 
                />
                <p className="text-xs text-gray-500 mt-1">Available: {selectedItem.quantity} {selectedItem.unit}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Work Order (Optional)</label>
                <input 
                  type="text" 
                  placeholder="WO-XXXX"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea 
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" 
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowIssueModal(false)} className="flex-1 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50">
                Cancel
              </button>
              <button onClick={() => setShowIssueModal(false)} className="flex-1 py-2 bg-[#198038] text-white rounded-lg font-medium hover:bg-[#166a2e]">
                Issue Stock
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
