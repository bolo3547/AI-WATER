'use client'

import { useState, useEffect } from 'react'
import { 
  MapPin, Plus, Trash2, Edit, Search, Filter, Globe, Building, 
  Map, X, AlertTriangle, Check, ChevronDown, ChevronRight 
} from 'lucide-react'

interface Country {
  id: string
  name: string
  code: string
  region: string
}

interface Town {
  id: string
  name: string
  country_id: string
  lat: number
  lng: number
  area_type: 'urban' | 'peri-urban' | 'rural'
  population?: number
  is_active: boolean
}

interface DMALocation {
  id: string
  name: string
  town_id: string
  lat: number
  lng: number
  area: string
  is_active: boolean
}

export default function LocationManagementPage() {
  // Countries
  const [countries, setCountries] = useState<Country[]>([
    { id: 'zm', name: 'Zambia', code: 'ZM', region: 'Southern Africa' },
    { id: 'zw', name: 'Zimbabwe', code: 'ZW', region: 'Southern Africa' },
    { id: 'bw', name: 'Botswana', code: 'BW', region: 'Southern Africa' },
    { id: 'mw', name: 'Malawi', code: 'MW', region: 'Southern Africa' },
    { id: 'mz', name: 'Mozambique', code: 'MZ', region: 'Southern Africa' },
  ])

  // Towns
  const [towns, setTowns] = useState<Town[]>([
    { id: 'lusaka', name: 'Lusaka', country_id: 'zm', lat: -15.4067, lng: 28.2872, area_type: 'urban', population: 2500000, is_active: true },
    { id: 'ndola', name: 'Ndola', country_id: 'zm', lat: -12.9587, lng: 28.6366, area_type: 'urban', population: 500000, is_active: true },
    { id: 'kitwe', name: 'Kitwe', country_id: 'zm', lat: -12.8024, lng: 28.2132, area_type: 'urban', population: 520000, is_active: true },
    { id: 'livingstone', name: 'Livingstone', country_id: 'zm', lat: -17.8419, lng: 25.8544, area_type: 'urban', population: 180000, is_active: false },
    { id: 'harare', name: 'Harare', country_id: 'zw', lat: -17.8292, lng: 31.0522, area_type: 'urban', population: 1600000, is_active: false },
    { id: 'gaborone', name: 'Gaborone', country_id: 'bw', lat: -24.6282, lng: 25.9231, area_type: 'urban', population: 230000, is_active: false },
  ])

  // DMAs/Locations within towns
  const [dmaLocations, setDmaLocations] = useState<DMALocation[]>([
    { id: 'dma-001', name: 'Kabulonga', town_id: 'lusaka', lat: -15.4192, lng: 28.3225, area: 'Residential High-Income', is_active: true },
    { id: 'dma-002', name: 'Woodlands', town_id: 'lusaka', lat: -15.4134, lng: 28.3064, area: 'Residential Mixed', is_active: true },
    { id: 'dma-003', name: 'Roma', town_id: 'lusaka', lat: -15.3958, lng: 28.3108, area: 'Residential Mid-Income', is_active: true },
    { id: 'dma-004', name: 'Chelstone', town_id: 'lusaka', lat: -15.3605, lng: 28.3517, area: 'Residential Large', is_active: true },
    { id: 'dma-005', name: 'Chilenje', town_id: 'lusaka', lat: -15.4433, lng: 28.2925, area: 'Residential Dense', is_active: true },
    { id: 'dma-006', name: 'Matero', town_id: 'lusaka', lat: -15.3747, lng: 28.2633, area: 'Residential High-Density', is_active: true },
    { id: 'dma-007', name: 'Kalingalinga', town_id: 'lusaka', lat: -15.4028, lng: 28.3350, area: 'Compound Urban', is_active: true },
    { id: 'dma-008', name: 'Olympia Park', town_id: 'lusaka', lat: -15.4089, lng: 28.2953, area: 'Residential Premium', is_active: true },
  ])

  // Modal states
  const [showCountryModal, setShowCountryModal] = useState(false)
  const [showTownModal, setShowTownModal] = useState(false)
  const [showDMAModal, setShowDMAModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  
  // Edit states
  const [editingCountry, setEditingCountry] = useState<Country | null>(null)
  const [editingTown, setEditingTown] = useState<Town | null>(null)
  const [editingDMA, setEditingDMA] = useState<DMALocation | null>(null)
  const [itemToDelete, setItemToDelete] = useState<{ type: 'country' | 'town' | 'dma', item: any } | null>(null)
  
  // Form states
  const [countryForm, setCountryForm] = useState({ name: '', code: '', region: 'Southern Africa' })
  const [townForm, setTownForm] = useState<{ name: string, country_id: string, lat: string, lng: string, area_type: 'urban' | 'peri-urban' | 'rural', population: string }>({ name: '', country_id: 'zm', lat: '', lng: '', area_type: 'urban', population: '' })
  const [dmaForm, setDmaForm] = useState({ name: '', town_id: 'lusaka', lat: '', lng: '', area: '' })
  
  // UI states
  const [activeTab, setActiveTab] = useState<'countries' | 'towns' | 'dmas'>('dmas')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedCountries, setExpandedCountries] = useState<string[]>(['zm'])
  
  // Handlers
  const handleAddCountry = () => {
    if (!countryForm.name || !countryForm.code) return
    const newCountry: Country = {
      id: countryForm.code.toLowerCase(),
      name: countryForm.name,
      code: countryForm.code.toUpperCase(),
      region: countryForm.region
    }
    if (editingCountry) {
      setCountries(countries.map(c => c.id === editingCountry.id ? newCountry : c))
    } else {
      setCountries([...countries, newCountry])
    }
    setShowCountryModal(false)
    setCountryForm({ name: '', code: '', region: 'Southern Africa' })
    setEditingCountry(null)
  }

  const handleAddTown = () => {
    if (!townForm.name || !townForm.country_id) return
    const newTown: Town = {
      id: townForm.name.toLowerCase().replace(/\s+/g, '-'),
      name: townForm.name,
      country_id: townForm.country_id,
      lat: parseFloat(townForm.lat) || 0,
      lng: parseFloat(townForm.lng) || 0,
      area_type: townForm.area_type,
      population: parseInt(townForm.population) || undefined,
      is_active: true
    }
    if (editingTown) {
      setTowns(towns.map(t => t.id === editingTown.id ? { ...newTown, id: editingTown.id } : t))
    } else {
      setTowns([...towns, newTown])
    }
    setShowTownModal(false)
    setTownForm({ name: '', country_id: 'zm', lat: '', lng: '', area_type: 'urban', population: '' })
    setEditingTown(null)
  }

  const handleAddDMA = () => {
    if (!dmaForm.name || !dmaForm.town_id) return
    const newDMA: DMALocation = {
      id: `dma-${String(dmaLocations.length + 1).padStart(3, '0')}`,
      name: dmaForm.name,
      town_id: dmaForm.town_id,
      lat: parseFloat(dmaForm.lat) || 0,
      lng: parseFloat(dmaForm.lng) || 0,
      area: dmaForm.area,
      is_active: true
    }
    if (editingDMA) {
      setDmaLocations(dmaLocations.map(d => d.id === editingDMA.id ? { ...newDMA, id: editingDMA.id } : d))
    } else {
      setDmaLocations([...dmaLocations, newDMA])
    }
    setShowDMAModal(false)
    setDmaForm({ name: '', town_id: 'lusaka', lat: '', lng: '', area: '' })
    setEditingDMA(null)
  }

  const handleDelete = () => {
    if (!itemToDelete) return
    switch (itemToDelete.type) {
      case 'country':
        setCountries(countries.filter(c => c.id !== itemToDelete.item.id))
        // Also remove related towns and DMAs
        const countryTowns = towns.filter(t => t.country_id === itemToDelete.item.id)
        setTowns(towns.filter(t => t.country_id !== itemToDelete.item.id))
        setDmaLocations(dmaLocations.filter(d => !countryTowns.some(t => t.id === d.town_id)))
        break
      case 'town':
        setTowns(towns.filter(t => t.id !== itemToDelete.item.id))
        setDmaLocations(dmaLocations.filter(d => d.town_id !== itemToDelete.item.id))
        break
      case 'dma':
        setDmaLocations(dmaLocations.filter(d => d.id !== itemToDelete.item.id))
        break
    }
    setShowDeleteModal(false)
    setItemToDelete(null)
  }

  const openEditCountry = (country: Country) => {
    setEditingCountry(country)
    setCountryForm({ name: country.name, code: country.code, region: country.region })
    setShowCountryModal(true)
  }

  const openEditTown = (town: Town) => {
    setEditingTown(town)
    setTownForm({
      name: town.name,
      country_id: town.country_id,
      lat: String(town.lat),
      lng: String(town.lng),
      area_type: town.area_type,
      population: town.population ? String(town.population) : ''
    })
    setShowTownModal(true)
  }

  const openEditDMA = (dma: DMALocation) => {
    setEditingDMA(dma)
    setDmaForm({
      name: dma.name,
      town_id: dma.town_id,
      lat: String(dma.lat),
      lng: String(dma.lng),
      area: dma.area
    })
    setShowDMAModal(true)
  }

  const toggleTownActive = (townId: string) => {
    setTowns(towns.map(t => t.id === townId ? { ...t, is_active: !t.is_active } : t))
  }

  const toggleDMAActive = (dmaId: string) => {
    setDmaLocations(dmaLocations.map(d => d.id === dmaId ? { ...d, is_active: !d.is_active } : d))
  }

  const getCountryById = (id: string) => countries.find(c => c.id === id)
  const getTownById = (id: string) => towns.find(t => t.id === id)
  const getTownsByCountry = (countryId: string) => towns.filter(t => t.country_id === countryId)
  const getDMAsByTown = (townId: string) => dmaLocations.filter(d => d.town_id === townId)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Location Management</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5 sm:mt-1">Manage countries, towns, and DMA zones</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button 
            onClick={() => { setEditingCountry(null); setCountryForm({ name: '', code: '', region: 'Southern Africa' }); setShowCountryModal(true) }}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors"
          >
            <Globe className="w-4 h-4" />
            Add Country
          </button>
          <button 
            onClick={() => { setEditingTown(null); setTownForm({ name: '', country_id: 'zm', lat: '', lng: '', area_type: 'urban', population: '' }); setShowTownModal(true) }}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors"
          >
            <Building className="w-4 h-4" />
            Add Town
          </button>
          <button 
            onClick={() => { setEditingDMA(null); setDmaForm({ name: '', town_id: 'lusaka', lat: '', lng: '', area: '' }); setShowDMAModal(true) }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/25"
          >
            <MapPin className="w-4 h-4" />
            Add DMA Zone
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Globe className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{countries.length}</p>
              <p className="text-xs text-slate-500">Countries</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Building className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{towns.length}</p>
              <p className="text-xs text-slate-500">Towns</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <MapPin className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{dmaLocations.length}</p>
              <p className="text-xs text-slate-500">DMA Zones</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-100 flex items-center justify-center">
              <Map className="w-5 h-5 text-cyan-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{towns.filter(t => t.is_active).length}</p>
              <p className="text-xs text-slate-500">Active Towns</p>
            </div>
          </div>
        </div>
      </div>

      {/* Location Hierarchy View */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Location Hierarchy</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search locations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm"
            />
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {countries.map((country) => {
            const countryTowns = getTownsByCountry(country.id)
            const isExpanded = expandedCountries.includes(country.id)
            
            return (
              <div key={country.id}>
                {/* Country Row */}
                <div className="flex items-center px-4 py-3 hover:bg-slate-50 transition-colors">
                  <button 
                    onClick={() => setExpandedCountries(
                      isExpanded 
                        ? expandedCountries.filter(id => id !== country.id)
                        : [...expandedCountries, country.id]
                    )}
                    className="p-1 mr-2"
                  >
                    {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                  </button>
                  <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center mr-3">
                    <Globe className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">{country.name}</p>
                    <p className="text-xs text-slate-500">{country.code} • {country.region} • {countryTowns.length} towns</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => openEditCountry(country)} className="p-1.5 hover:bg-slate-100 rounded-lg">
                      <Edit className="w-4 h-4 text-slate-500" />
                    </button>
                    <button 
                      onClick={() => { setItemToDelete({ type: 'country', item: country }); setShowDeleteModal(true) }}
                      className="p-1.5 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>

                {/* Towns under this country */}
                {isExpanded && countryTowns.map((town) => {
                  const townDMAs = getDMAsByTown(town.id)
                  
                  return (
                    <div key={town.id}>
                      {/* Town Row */}
                      <div className="flex items-center px-4 py-3 pl-12 hover:bg-slate-50 transition-colors border-l-2 border-blue-200 ml-6">
                        <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center mr-3">
                          <Building className="w-4 h-4 text-emerald-600" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-slate-900">{town.name}</p>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              town.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                            }`}>
                              {town.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500">
                            {town.area_type} • {town.population?.toLocaleString() || 'N/A'} pop • {townDMAs.length} DMAs
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <button 
                            onClick={() => toggleTownActive(town.id)}
                            className={`p-1.5 rounded-lg transition-colors ${town.is_active ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}
                            title={town.is_active ? 'Deactivate' : 'Activate'}
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button onClick={() => openEditTown(town)} className="p-1.5 hover:bg-slate-100 rounded-lg">
                            <Edit className="w-4 h-4 text-slate-500" />
                          </button>
                          <button 
                            onClick={() => { setItemToDelete({ type: 'town', item: town }); setShowDeleteModal(true) }}
                            className="p-1.5 hover:bg-red-50 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>

                      {/* DMAs under this town */}
                      {townDMAs.map((dma) => (
                        <div key={dma.id} className="flex items-center px-4 py-2.5 pl-20 hover:bg-slate-50 transition-colors border-l-2 border-emerald-200 ml-12">
                          <div className="w-6 h-6 rounded bg-purple-100 flex items-center justify-center mr-3">
                            <MapPin className="w-3 h-3 text-purple-600" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-slate-900">{dma.name}</p>
                            <p className="text-xs text-slate-500">{dma.area}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400 font-mono">
                              {dma.lat.toFixed(4)}, {dma.lng.toFixed(4)}
                            </span>
                            <button 
                              onClick={() => toggleDMAActive(dma.id)}
                              className={`p-1 rounded transition-colors ${dma.is_active ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}
                            >
                              <Check className="w-3 h-3" />
                            </button>
                            <button onClick={() => openEditDMA(dma)} className="p-1 hover:bg-slate-100 rounded">
                              <Edit className="w-3 h-3 text-slate-500" />
                            </button>
                            <button 
                              onClick={() => { setItemToDelete({ type: 'dma', item: dma }); setShowDeleteModal(true) }}
                              className="p-1 hover:bg-red-50 rounded"
                            >
                              <Trash2 className="w-3 h-3 text-red-500" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>

      {/* Add/Edit Country Modal */}
      {showCountryModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-900">
                {editingCountry ? 'Edit Country' : 'Add New Country'}
              </h2>
              <button onClick={() => setShowCountryModal(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Country Name</label>
                <input 
                  type="text" 
                  value={countryForm.name}
                  onChange={(e) => setCountryForm({ ...countryForm, name: e.target.value })}
                  placeholder="e.g. South Africa"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Country Code (ISO)</label>
                <input 
                  type="text" 
                  value={countryForm.code}
                  onChange={(e) => setCountryForm({ ...countryForm, code: e.target.value.toUpperCase() })}
                  placeholder="e.g. ZA"
                  maxLength={2}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 uppercase" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Region</label>
                <select 
                  value={countryForm.region}
                  onChange={(e) => setCountryForm({ ...countryForm, region: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="Southern Africa">Southern Africa</option>
                  <option value="East Africa">East Africa</option>
                  <option value="West Africa">West Africa</option>
                  <option value="Central Africa">Central Africa</option>
                  <option value="North Africa">North Africa</option>
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setShowCountryModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                  Cancel
                </button>
                <button onClick={handleAddCountry} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  {editingCountry ? 'Update' : 'Add Country'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Town Modal */}
      {showTownModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-900">
                {editingTown ? 'Edit Town' : 'Add New Town'}
              </h2>
              <button onClick={() => setShowTownModal(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Town Name</label>
                <input 
                  type="text" 
                  value={townForm.name}
                  onChange={(e) => setTownForm({ ...townForm, name: e.target.value })}
                  placeholder="e.g. Kabwe"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Country</label>
                <select 
                  value={townForm.country_id}
                  onChange={(e) => setTownForm({ ...townForm, country_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  {countries.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Latitude</label>
                  <input 
                    type="text" 
                    value={townForm.lat}
                    onChange={(e) => setTownForm({ ...townForm, lat: e.target.value })}
                    placeholder="-15.4067"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Longitude</label>
                  <input 
                    type="text" 
                    value={townForm.lng}
                    onChange={(e) => setTownForm({ ...townForm, lng: e.target.value })}
                    placeholder="28.2872"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Area Type</label>
                  <select 
                    value={townForm.area_type}
                    onChange={(e) => setTownForm({ ...townForm, area_type: e.target.value as any })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="urban">Urban</option>
                    <option value="peri-urban">Peri-Urban</option>
                    <option value="rural">Rural</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Population</label>
                  <input 
                    type="number" 
                    value={townForm.population}
                    onChange={(e) => setTownForm({ ...townForm, population: e.target.value })}
                    placeholder="500000"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                  />
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setShowTownModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                  Cancel
                </button>
                <button onClick={handleAddTown} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  {editingTown ? 'Update' : 'Add Town'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit DMA Modal */}
      {showDMAModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-slate-900">
                {editingDMA ? 'Edit DMA Zone' : 'Add New DMA Zone'}
              </h2>
              <button onClick={() => setShowDMAModal(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">DMA/Zone Name</label>
                <input 
                  type="text" 
                  value={dmaForm.name}
                  onChange={(e) => setDmaForm({ ...dmaForm, name: e.target.value })}
                  placeholder="e.g. Northmead"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Town</label>
                <select 
                  value={dmaForm.town_id}
                  onChange={(e) => setDmaForm({ ...dmaForm, town_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  {towns.map(t => (
                    <option key={t.id} value={t.id}>{t.name} ({getCountryById(t.country_id)?.name})</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Latitude</label>
                  <input 
                    type="text" 
                    value={dmaForm.lat}
                    onChange={(e) => setDmaForm({ ...dmaForm, lat: e.target.value })}
                    placeholder="-15.4192"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Longitude</label>
                  <input 
                    type="text" 
                    value={dmaForm.lng}
                    onChange={(e) => setDmaForm({ ...dmaForm, lng: e.target.value })}
                    placeholder="28.3225"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Area Description</label>
                <input 
                  type="text" 
                  value={dmaForm.area}
                  onChange={(e) => setDmaForm({ ...dmaForm, area: e.target.value })}
                  placeholder="e.g. Residential High-Income"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500" 
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button onClick={() => setShowDMAModal(false)} className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                  Cancel
                </button>
                <button onClick={handleAddDMA} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  {editingDMA ? 'Update' : 'Add DMA Zone'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && itemToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Delete {itemToDelete.type.charAt(0).toUpperCase() + itemToDelete.type.slice(1)}</h2>
            </div>
            
            <p className="text-slate-600 mb-4">
              Are you sure you want to delete <strong>{itemToDelete.item.name}</strong>?
              {itemToDelete.type === 'country' && ' This will also delete all towns and DMAs in this country.'}
              {itemToDelete.type === 'town' && ' This will also delete all DMAs in this town.'}
            </p>
            
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-700">
                <strong>Warning:</strong> This action cannot be undone.
              </p>
            </div>
            
            <div className="flex gap-3">
              <button 
                onClick={() => { setShowDeleteModal(false); setItemToDelete(null) }} 
                className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button 
                onClick={handleDelete}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
