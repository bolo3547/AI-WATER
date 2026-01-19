'use client'

import { useState, useEffect } from 'react'
import { 
  CloudRain, Sun, Cloud, Thermometer, Wind, Droplets,
  AlertTriangle, TrendingUp, TrendingDown, Calendar,
  RefreshCw, BarChart3, Activity, Zap, Eye
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Select } from '@/components/ui/Controls'

interface WeatherData {
  date: string
  condition: 'sunny' | 'cloudy' | 'rainy' | 'storm'
  temperature: number
  humidity: number
  rainfall: number
  windSpeed: number
  uvIndex: number
}

interface CorrelationData {
  weather: string
  avgDemand: number
  avgNRW: number
  avgPressure: number
  incidents: number
  correlation: number
}

interface Forecast {
  date: string
  predictedDemand: number
  predictedNRW: number
  confidence: number
  weather: string
  recommendation: string
}

export default function WeatherPage() {
  const [currentWeather, setCurrentWeather] = useState<WeatherData | null>(null)
  const [weeklyForecast, setWeeklyForecast] = useState<WeatherData[]>([])
  const [correlations, setCorrelations] = useState<CorrelationData[]>([])
  const [demandForecast, setDemandForecast] = useState<Forecast[]>([])
  const [timeRange, setTimeRange] = useState('7')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [timeRange])

  const loadData = () => {
    setIsLoading(true)
    setTimeout(() => {
      setCurrentWeather({
        date: new Date().toISOString().split('T')[0],
        condition: 'sunny',
        temperature: 28,
        humidity: 65,
        rainfall: 0,
        windSpeed: 12,
        uvIndex: 7
      })

      setWeeklyForecast([
        { date: '2026-01-30', condition: 'sunny', temperature: 29, humidity: 60, rainfall: 0, windSpeed: 10, uvIndex: 8 },
        { date: '2026-01-31', condition: 'cloudy', temperature: 27, humidity: 70, rainfall: 0, windSpeed: 15, uvIndex: 5 },
        { date: '2026-02-01', condition: 'rainy', temperature: 24, humidity: 85, rainfall: 25, windSpeed: 20, uvIndex: 2 },
        { date: '2026-02-02', condition: 'rainy', temperature: 23, humidity: 90, rainfall: 45, windSpeed: 25, uvIndex: 1 },
        { date: '2026-02-03', condition: 'storm', temperature: 22, humidity: 95, rainfall: 80, windSpeed: 35, uvIndex: 0 },
        { date: '2026-02-04', condition: 'cloudy', temperature: 25, humidity: 75, rainfall: 5, windSpeed: 18, uvIndex: 4 },
        { date: '2026-02-05', condition: 'sunny', temperature: 28, humidity: 65, rainfall: 0, windSpeed: 12, uvIndex: 7 }
      ])

      setCorrelations([
        { weather: 'Hot & Dry (>30°C)', avgDemand: 145000, avgNRW: 42, avgPressure: 2.8, incidents: 12, correlation: 0.85 },
        { weather: 'Warm (25-30°C)', avgDemand: 125000, avgNRW: 38, avgPressure: 3.2, incidents: 8, correlation: 0.72 },
        { weather: 'Moderate (20-25°C)', avgDemand: 110000, avgNRW: 35, avgPressure: 3.5, incidents: 5, correlation: 0.45 },
        { weather: 'Rainy (<50mm)', avgDemand: 95000, avgNRW: 32, avgPressure: 3.8, incidents: 4, correlation: -0.38 },
        { weather: 'Heavy Rain (>50mm)', avgDemand: 85000, avgNRW: 28, avgPressure: 4.0, incidents: 15, correlation: -0.65 }
      ])

      setDemandForecast([
        {
          date: '2026-01-30',
          predictedDemand: 128000,
          predictedNRW: 39,
          confidence: 92,
          weather: 'Sunny, 29°C',
          recommendation: 'Increase pressure during morning peak hours'
        },
        {
          date: '2026-01-31',
          predictedDemand: 122000,
          predictedNRW: 37,
          confidence: 88,
          weather: 'Cloudy, 27°C',
          recommendation: 'Normal operations'
        },
        {
          date: '2026-02-01',
          predictedDemand: 98000,
          predictedNRW: 33,
          confidence: 85,
          weather: 'Rain expected',
          recommendation: 'Monitor for flooding, reduce night pressure'
        },
        {
          date: '2026-02-02',
          predictedDemand: 90000,
          predictedNRW: 30,
          confidence: 82,
          weather: 'Heavy rain',
          recommendation: 'Dispatch crews for flood response, check drainage'
        },
        {
          date: '2026-02-03',
          predictedDemand: 88000,
          predictedNRW: 45,
          confidence: 75,
          weather: 'Storm warning',
          recommendation: '⚠️ Alert: High incident risk. Pre-position repair crews.'
        }
      ])

      setIsLoading(false)
    }, 1000)
  }

  const getWeatherIcon = (condition: string, size: string = 'w-8 h-8') => {
    switch (condition) {
      case 'sunny': return <Sun className={`${size} text-yellow-500`} />
      case 'cloudy': return <Cloud className={`${size} text-gray-500`} />
      case 'rainy': return <CloudRain className={`${size} text-blue-500`} />
      case 'storm': return <CloudRain className={`${size} text-purple-500`} />
      default: return <Cloud className={`${size} text-gray-500`} />
    }
  }

  const getCorrelationColor = (correlation: number) => {
    if (correlation > 0.6) return 'text-red-600'
    if (correlation > 0.3) return 'text-orange-600'
    if (correlation > 0) return 'text-yellow-600'
    if (correlation > -0.3) return 'text-blue-600'
    return 'text-green-600'
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <CloudRain className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" />
            Weather Correlation
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            AI analysis of weather impact on water demand and NRW
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={timeRange}
            options={[
              { value: '7', label: '7 Days' },
              { value: '14', label: '14 Days' },
              { value: '30', label: '30 Days' }
            ]}
            onChange={setTimeRange}
          />
          <Button variant="secondary" onClick={loadData} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Current Weather */}
      {currentWeather && (
        <div className="bg-gradient-to-r from-blue-500 via-cyan-500 to-sky-500 rounded-xl p-4 sm:p-6 text-white">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              {getWeatherIcon(currentWeather.condition, 'w-16 h-16')}
              <div>
                <p className="text-blue-100 text-sm">Current Weather in Lusaka</p>
                <p className="text-4xl font-bold">{currentWeather.temperature}°C</p>
                <p className="text-blue-100 capitalize">{currentWeather.condition}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div className="bg-white/20 rounded-lg p-3">
                <Droplets className="w-5 h-5 mx-auto mb-1" />
                <p className="text-xl font-bold">{currentWeather.humidity}%</p>
                <p className="text-xs text-blue-100">Humidity</p>
              </div>
              <div className="bg-white/20 rounded-lg p-3">
                <CloudRain className="w-5 h-5 mx-auto mb-1" />
                <p className="text-xl font-bold">{currentWeather.rainfall}mm</p>
                <p className="text-xs text-blue-100">Rainfall</p>
              </div>
              <div className="bg-white/20 rounded-lg p-3">
                <Wind className="w-5 h-5 mx-auto mb-1" />
                <p className="text-xl font-bold">{currentWeather.windSpeed}</p>
                <p className="text-xs text-blue-100">km/h Wind</p>
              </div>
              <div className="bg-white/20 rounded-lg p-3">
                <Sun className="w-5 h-5 mx-auto mb-1" />
                <p className="text-xl font-bold">{currentWeather.uvIndex}</p>
                <p className="text-xs text-blue-100">UV Index</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7-Day Forecast */}
      <SectionCard title="7-Day Forecast" subtitle="Weather outlook and predicted impact">
        <div className="flex gap-3 overflow-x-auto pb-2">
          {weeklyForecast.map((day, idx) => (
            <div 
              key={idx}
              className={`flex-shrink-0 w-28 rounded-xl p-3 text-center ${
                day.condition === 'storm' ? 'bg-purple-50 border-2 border-purple-200' :
                day.condition === 'rainy' ? 'bg-blue-50' :
                day.condition === 'cloudy' ? 'bg-slate-50' : 'bg-yellow-50'
              }`}
            >
              <p className="text-xs text-slate-500 mb-2">
                {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
              </p>
              {getWeatherIcon(day.condition, 'w-10 h-10 mx-auto')}
              <p className="text-lg font-bold text-slate-900 mt-2">{day.temperature}°C</p>
              <p className="text-xs text-slate-500 capitalize">{day.condition}</p>
              {day.rainfall > 0 && (
                <p className="text-xs text-blue-600 mt-1">{day.rainfall}mm rain</p>
              )}
              {day.condition === 'storm' && (
                <span className="inline-block mt-2 px-2 py-0.5 bg-purple-100 text-purple-700 text-[10px] rounded">
                  ⚠️ Warning
                </span>
              )}
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Weather-NRW Correlation */}
        <SectionCard title="Weather-NRW Correlation" subtitle="Historical analysis of weather impact">
          <div className="space-y-3">
            {correlations.map((corr, idx) => (
              <div key={idx} className="bg-slate-50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-slate-900">{corr.weather}</span>
                  <span className={`font-bold ${getCorrelationColor(corr.correlation)}`}>
                    {corr.correlation > 0 ? '+' : ''}{(corr.correlation * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div>
                    <p className="font-semibold text-slate-700">{(corr.avgDemand / 1000).toFixed(0)}K</p>
                    <p className="text-slate-500">m³/day</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-700">{corr.avgNRW}%</p>
                    <p className="text-slate-500">NRW</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-700">{corr.avgPressure}</p>
                    <p className="text-slate-500">bar</p>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-700">{corr.incidents}</p>
                    <p className="text-slate-500">incidents</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
            <p className="font-semibold">Key Insight:</p>
            <p>Hot weather correlates with +85% higher demand and +18% NRW increase. Heavy rain reduces demand but increases pipe burst incidents by 3x.</p>
          </div>
        </SectionCard>

        {/* Demand Forecast */}
        <SectionCard title="AI Demand Forecast" subtitle="Weather-adjusted predictions">
          <div className="space-y-3">
            {demandForecast.map((forecast, idx) => (
              <div key={idx} className={`rounded-lg p-3 ${
                forecast.recommendation.includes('⚠️') ? 'bg-red-50 border border-red-200' : 'bg-slate-50'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-900">
                      {new Date(forecast.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">{forecast.weather}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center mb-2">
                  <div className="bg-white rounded p-2">
                    <p className="text-lg font-bold text-slate-900">{(forecast.predictedDemand / 1000).toFixed(0)}K</p>
                    <p className="text-[10px] text-slate-500">m³ demand</p>
                  </div>
                  <div className="bg-white rounded p-2">
                    <p className="text-lg font-bold text-orange-600">{forecast.predictedNRW}%</p>
                    <p className="text-[10px] text-slate-500">predicted NRW</p>
                  </div>
                  <div className="bg-white rounded p-2">
                    <p className="text-lg font-bold text-green-600">{forecast.confidence}%</p>
                    <p className="text-[10px] text-slate-500">confidence</p>
                  </div>
                </div>
                <p className={`text-xs ${forecast.recommendation.includes('⚠️') ? 'text-red-700 font-semibold' : 'text-slate-600'}`}>
                  💡 {forecast.recommendation}
                </p>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      {/* Storm Warning */}
      {weeklyForecast.some(d => d.condition === 'storm') && (
        <div className="bg-gradient-to-r from-purple-600 to-red-600 rounded-xl p-4 sm:p-6 text-white">
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-10 h-10 flex-shrink-0 animate-pulse" />
            <div>
              <h3 className="text-lg font-bold">⚠️ Storm Warning - February 3rd</h3>
              <p className="text-purple-100 mt-1">
                Heavy rainfall (80mm) and strong winds (35 km/h) expected. Historical data shows 3x increase in pipe burst incidents during such conditions.
              </p>
              <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-white/20 rounded-lg p-2 text-center">
                  <p className="text-xl font-bold">80mm</p>
                  <p className="text-xs">Expected Rain</p>
                </div>
                <div className="bg-white/20 rounded-lg p-2 text-center">
                  <p className="text-xl font-bold">35km/h</p>
                  <p className="text-xs">Wind Speed</p>
                </div>
                <div className="bg-white/20 rounded-lg p-2 text-center">
                  <p className="text-xl font-bold">15</p>
                  <p className="text-xs">Predicted Incidents</p>
                </div>
                <div className="bg-white/20 rounded-lg p-2 text-center">
                  <p className="text-xl font-bold">45%</p>
                  <p className="text-xs">NRW Spike Risk</p>
                </div>
              </div>
              <Button variant="secondary" className="mt-4 bg-white/20 hover:bg-white/30 text-white border-0">
                <Eye className="w-4 h-4" />
                View Emergency Plan
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
