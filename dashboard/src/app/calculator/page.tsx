'use client'

import { useState, useEffect, useMemo } from 'react'
import { 
  Calculator, DollarSign, Droplets, TrendingUp, TrendingDown,
  Info, Download, Settings, ChevronDown, RefreshCw,
  PiggyBank, Target, Clock, Zap, AlertTriangle
} from 'lucide-react'

export default function CalculatorPage() {
  // Input parameters
  const [systemInput, setSystemInput] = useState(125000) // m³/day
  const [currentNRW, setCurrentNRW] = useState(32.4) // %
  const [targetNRW, setTargetNRW] = useState(25) // %
  const [waterTariff, setWaterTariff] = useState(8.5) // ZMW per m³
  const [operationalCost, setOperationalCost] = useState(2.1) // ZMW per m³
  const [investmentCost, setInvestmentCost] = useState(2500000) // ZMW
  const [implementationMonths, setImplementationMonths] = useState(18)

  // Calculate results
  const results = useMemo(() => {
    // Current water loss
    const currentLossDaily = systemInput * (currentNRW / 100) // m³/day
    const currentLossAnnual = currentLossDaily * 365 // m³/year

    // Target water loss
    const targetLossDaily = systemInput * (targetNRW / 100)
    const targetLossAnnual = targetLossDaily * 365

    // Water saved
    const waterSavedDaily = currentLossDaily - targetLossDaily
    const waterSavedAnnual = currentLossAnnual - targetLossAnnual

    // Revenue calculations
    const currentRevenueLostDaily = currentLossDaily * waterTariff
    const currentRevenueLostAnnual = currentRevenueLostDaily * 365

    const revenueSavedDaily = waterSavedDaily * waterTariff
    const revenueSavedAnnual = waterSavedAnnual * waterTariff

    // Operational savings (reduced pumping, treatment)
    const operationalSavingsAnnual = waterSavedAnnual * operationalCost

    // Total financial benefit
    const totalBenefitAnnual = revenueSavedAnnual + operationalSavingsAnnual

    // ROI calculations
    const paybackMonths = (investmentCost / (totalBenefitAnnual / 12))
    const roi5Year = ((totalBenefitAnnual * 5) - investmentCost) / investmentCost * 100
    const npv5Year = (totalBenefitAnnual * 5) - investmentCost // Simplified NPV

    return {
      currentLossDaily,
      currentLossAnnual,
      waterSavedDaily,
      waterSavedAnnual,
      currentRevenueLostAnnual,
      revenueSavedAnnual,
      operationalSavingsAnnual,
      totalBenefitAnnual,
      paybackMonths,
      roi5Year,
      npv5Year,
      nrwReduction: currentNRW - targetNRW,
    }
  }, [systemInput, currentNRW, targetNRW, waterTariff, operationalCost, investmentCost])

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `K${(value / 1000000).toFixed(2)}M`
    } else if (value >= 1000) {
      return `K${(value / 1000).toFixed(0)}k`
    }
    return `K${value.toFixed(0)}`
  }

  // Format number with commas
  const formatNumber = (value: number) => {
    return value.toLocaleString('en-US', { maximumFractionDigits: 0 })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-2 sm:p-3 md:p-4 lg:p-6">
      {/* Header */}
      <div className="mb-2 sm:mb-3 md:mb-4 lg:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
          <div>
            <h1 className="text-base sm:text-lg md:text-xl lg:text-3xl font-bold text-slate-900">Financial Calculator</h1>
            <p className="text-[10px] sm:text-xs md:text-sm text-slate-500 mt-0.5">Calculate ROI from NRW reduction</p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs sm:text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
              <RefreshCw className="w-4 h-4" />
              Reset
            </button>
            <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-xs sm:text-sm font-medium hover:bg-blue-700 transition-colors">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
        {/* Input Parameters */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <Settings className="w-4 h-4 text-blue-600" />
              </div>
              <h2 className="text-sm sm:text-base font-semibold text-slate-900">Input Parameters</h2>
            </div>

            <div className="space-y-4">
              {/* System Input Volume */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-700 mb-1">
                  System Input Volume (m³/day)
                </label>
                <input
                  type="number"
                  value={systemInput}
                  onChange={(e) => setSystemInput(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-[10px] text-slate-400 mt-1">Total water entering the distribution system</p>
              </div>

              {/* Current NRW */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-700 mb-1">
                  Current NRW Rate (%)
                </label>
                <div className="relative">
                  <input
                    type="range"
                    min="0"
                    max="70"
                    step="0.1"
                    value={currentNRW}
                    onChange={(e) => setCurrentNRW(Number(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-red-500"
                  />
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-slate-400">0%</span>
                    <span className="text-sm font-bold text-red-600">{currentNRW.toFixed(1)}%</span>
                    <span className="text-[10px] text-slate-400">70%</span>
                  </div>
                </div>
              </div>

              {/* Target NRW */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-700 mb-1">
                  Target NRW Rate (%)
                </label>
                <div className="relative">
                  <input
                    type="range"
                    min="0"
                    max="70"
                    step="0.1"
                    value={targetNRW}
                    onChange={(e) => setTargetNRW(Number(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                  />
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-slate-400">0%</span>
                    <span className="text-sm font-bold text-emerald-600">{targetNRW.toFixed(1)}%</span>
                    <span className="text-[10px] text-slate-400">70%</span>
                  </div>
                </div>
              </div>

              {/* Water Tariff */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-700 mb-1">
                  Water Tariff (ZMW/m³)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={waterTariff}
                  onChange={(e) => setWaterTariff(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Operational Cost */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-700 mb-1">
                  Operational Cost (ZMW/m³)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={operationalCost}
                  onChange={(e) => setOperationalCost(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-[10px] text-slate-400 mt-1">Pumping, treatment, chemicals</p>
              </div>

              {/* Investment Cost */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-slate-700 mb-1">
                  Investment Cost (ZMW)
                </label>
                <input
                  type="number"
                  value={investmentCost}
                  onChange={(e) => setInvestmentCost(Number(e.target.value))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-[10px] text-slate-400 mt-1">Sensors, software, installation</p>
              </div>
            </div>
          </div>

          {/* Quick Presets */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
            <h3 className="text-xs sm:text-sm font-semibold text-slate-900 mb-3">Quick Scenarios</h3>
            <div className="space-y-2">
              <button 
                onClick={() => { setCurrentNRW(40); setTargetNRW(30); setInvestmentCost(1500000); }}
                className="w-full p-2 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <p className="text-xs font-medium text-slate-900">Conservative</p>
                <p className="text-[10px] text-slate-500">40% → 30% | K1.5M investment</p>
              </button>
              <button 
                onClick={() => { setCurrentNRW(45); setTargetNRW(25); setInvestmentCost(3000000); }}
                className="w-full p-2 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <p className="text-xs font-medium text-slate-900">Moderate</p>
                <p className="text-[10px] text-slate-500">45% → 25% | K3M investment</p>
              </button>
              <button 
                onClick={() => { setCurrentNRW(50); setTargetNRW(20); setInvestmentCost(5000000); }}
                className="w-full p-2 text-left bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <p className="text-xs font-medium text-slate-900">Aggressive</p>
                <p className="text-[10px] text-slate-500">50% → 20% | K5M investment</p>
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-4">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl sm:rounded-2xl p-2 sm:p-3 md:p-4 text-white">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <PiggyBank className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 opacity-80" />
                <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4" />
              </div>
              <p className="text-[8px] sm:text-[10px] md:text-xs text-green-100">Annual Savings</p>
              <p className="text-sm sm:text-lg md:text-xl lg:text-2xl font-bold">{formatCurrency(results.totalBenefitAnnual)}</p>
            </div>
            
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl sm:rounded-2xl p-2 sm:p-3 md:p-4 text-white">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <Clock className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 opacity-80" />
                <span className="text-[8px] sm:text-[10px] md:text-xs px-1.5 sm:px-2 py-0.5 bg-white/20 rounded-full">ROI</span>
              </div>
              <p className="text-[8px] sm:text-[10px] md:text-xs text-blue-100">Payback</p>
              <p className="text-sm sm:text-lg md:text-xl lg:text-2xl font-bold">{results.paybackMonths.toFixed(1)} <span className="text-[10px] sm:text-xs md:text-sm font-normal">mo</span></p>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl sm:rounded-2xl p-2 sm:p-3 md:p-4 text-white">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <Target className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 opacity-80" />
                <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4" />
              </div>
              <p className="text-[8px] sm:text-[10px] md:text-xs text-purple-100">NRW Reduction</p>
              <p className="text-sm sm:text-lg md:text-xl lg:text-2xl font-bold">{results.nrwReduction.toFixed(1)}%</p>
            </div>

            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl sm:rounded-2xl p-2 sm:p-3 md:p-4 text-white">
              <div className="flex items-center justify-between mb-1 sm:mb-2">
                <Zap className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 opacity-80" />
                <span className="text-[8px] sm:text-[10px] md:text-xs">{results.roi5Year > 0 ? '+' : ''}{results.roi5Year.toFixed(0)}%</span>
              </div>
              <p className="text-[8px] sm:text-[10px] md:text-xs text-orange-100">5-Year ROI</p>
              <p className="text-sm sm:text-lg md:text-xl lg:text-2xl font-bold">{formatCurrency(results.npv5Year)}</p>
            </div>
          </div>

          {/* Detailed Breakdown */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">Financial Breakdown</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Water Loss */}
              <div className="p-4 bg-red-50 rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <h4 className="text-xs sm:text-sm font-semibold text-red-900">Current Water Loss</h4>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-red-700">Daily Loss</span>
                    <span className="font-semibold text-red-900">{formatNumber(results.currentLossDaily)} m³</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-red-700">Annual Loss</span>
                    <span className="font-semibold text-red-900">{formatNumber(results.currentLossAnnual)} m³</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm pt-2 border-t border-red-200">
                    <span className="text-red-700">Revenue Lost/Year</span>
                    <span className="font-bold text-red-900">{formatCurrency(results.currentRevenueLostAnnual)}</span>
                  </div>
                </div>
              </div>

              {/* Savings */}
              <div className="p-4 bg-emerald-50 rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <DollarSign className="w-4 h-4 text-emerald-600" />
                  <h4 className="text-xs sm:text-sm font-semibold text-emerald-900">Projected Savings</h4>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-emerald-700">Water Saved/Day</span>
                    <span className="font-semibold text-emerald-900">{formatNumber(results.waterSavedDaily)} m³</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-emerald-700">Revenue Saved/Year</span>
                    <span className="font-semibold text-emerald-900">{formatCurrency(results.revenueSavedAnnual)}</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm">
                    <span className="text-emerald-700">Operational Savings</span>
                    <span className="font-semibold text-emerald-900">{formatCurrency(results.operationalSavingsAnnual)}</span>
                  </div>
                  <div className="flex justify-between text-xs sm:text-sm pt-2 border-t border-emerald-200">
                    <span className="text-emerald-700">Total Annual Benefit</span>
                    <span className="font-bold text-emerald-900">{formatCurrency(results.totalBenefitAnnual)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 5-Year Projection */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">5-Year Cumulative Benefit</h3>
            
            <div className="h-48 flex items-end justify-between gap-2 sm:gap-3 mb-4">
              {[1, 2, 3, 4, 5].map((year) => {
                const yearBenefit = results.totalBenefitAnnual * year
                const cumulative = yearBenefit - investmentCost
                const isPositive = cumulative > 0
                const maxBenefit = results.totalBenefitAnnual * 5
                const height = Math.abs(yearBenefit) / maxBenefit * 100

                return (
                  <div key={year} className="flex-1 flex flex-col items-center gap-1">
                    <span className={`text-[9px] sm:text-xs font-semibold ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
                      {formatCurrency(cumulative)}
                    </span>
                    <div 
                      className={`w-full rounded-t-lg transition-all ${
                        isPositive ? 'bg-emerald-500' : 'bg-emerald-200'
                      }`}
                      style={{ height: `${height}%`, minHeight: '20px' }}
                    />
                    <span className="text-[10px] sm:text-xs text-slate-500">Y{year}</span>
                  </div>
                )
              })}
            </div>

            {/* Investment Line */}
            <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-amber-500 rounded-full" />
                <span className="text-xs sm:text-sm text-amber-700">Initial Investment</span>
              </div>
              <span className="text-sm font-bold text-amber-900">{formatCurrency(investmentCost)}</span>
            </div>
          </div>

          {/* Benefits Summary */}
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-4 sm:p-6 shadow-sm text-white">
            <h3 className="text-sm sm:text-base font-semibold mb-4">Investment Summary</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <p className="text-[10px] sm:text-xs text-blue-200">Investment</p>
                <p className="text-base sm:text-xl font-bold">{formatCurrency(investmentCost)}</p>
              </div>
              <div>
                <p className="text-[10px] sm:text-xs text-blue-200">Annual Return</p>
                <p className="text-base sm:text-xl font-bold">{formatCurrency(results.totalBenefitAnnual)}</p>
              </div>
              <div>
                <p className="text-[10px] sm:text-xs text-blue-200">Payback</p>
                <p className="text-base sm:text-xl font-bold">{results.paybackMonths.toFixed(1)} mo</p>
              </div>
              <div>
                <p className="text-[10px] sm:text-xs text-blue-200">5-Year Net Gain</p>
                <p className="text-base sm:text-xl font-bold">{formatCurrency(results.npv5Year)}</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-blue-500/30">
              <p className="text-xs sm:text-sm text-blue-100">
                With a {results.nrwReduction.toFixed(1)}% NRW reduction, the system pays for itself in{' '}
                <span className="font-bold text-white">{results.paybackMonths.toFixed(1)} months</span> and generates{' '}
                <span className="font-bold text-white">{formatCurrency(results.npv5Year)}</span> net benefit over 5 years.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
