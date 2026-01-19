'use client'

import { 
  LineChart, 
  Line, 
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts'

interface ChartDataPoint {
  timestamp: string
  [key: string]: string | number | undefined
}

// Custom tooltip for professional look
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null
  
  return (
    <div className="bg-white border border-surface-border rounded-lg shadow-soft p-3">
      <p className="text-caption text-text-tertiary mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-body font-medium" style={{ color: entry.color }}>
          {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
        </p>
      ))}
    </div>
  )
}

interface NRWTrendChartProps {
  data: ChartDataPoint[]
  height?: number
  showLegend?: boolean
}

export function NRWTrendChart({ data, height = 300, showLegend = false }: NRWTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="nrwGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#1e40af" stopOpacity={0.1}/>
            <stop offset="95%" stopColor="#1e40af" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis 
          dataKey="timestamp" 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 11 }}
        />
        <YAxis 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 11 }}
          tickFormatter={(value) => `${value}%`}
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend />}
        <Area 
          type="monotone" 
          dataKey="nrw" 
          stroke="#1e40af" 
          strokeWidth={2}
          fill="url(#nrwGradient)"
          name="NRW %"
        />
        {data[0]?.target !== undefined && (
          <Line 
            type="monotone" 
            dataKey="target" 
            stroke="#f59e0b" 
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Target"
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  )
}

interface WaterBalanceChartProps {
  data: { name: string; value: number; color: string }[]
  height?: number
}

export function WaterBalanceChart({ data, height = 300 }: WaterBalanceChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 10, right: 10, left: 100, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={true} vertical={false} />
        <XAxis 
          type="number"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 11 }}
          tickFormatter={(value) => `${value.toLocaleString()} m³`}
        />
        <YAxis 
          type="category"
          dataKey="name"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#374151', fontSize: 12, fontWeight: 500 }}
          width={90}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar 
          dataKey="value" 
          radius={[0, 4, 4, 0]}
          fill="#1e40af"
        >
          {data.map((entry, index) => (
            <rect key={`bar-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

interface FlowComparisonChartProps {
  data: ChartDataPoint[]
  height?: number
}

export function FlowComparisonChart({ data, height = 300 }: FlowComparisonChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis 
          dataKey="timestamp" 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 11 }}
        />
        <YAxis 
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 11 }}
          tickFormatter={(value) => `${value} m³/h`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          verticalAlign="top" 
          height={36}
          formatter={(value) => <span className="text-caption text-text-secondary">{value}</span>}
        />
        <Line 
          type="monotone" 
          dataKey="inflow" 
          stroke="#1e40af" 
          strokeWidth={2}
          dot={false}
          name="Inflow"
        />
        <Line 
          type="monotone" 
          dataKey="consumption" 
          stroke="#059669" 
          strokeWidth={2}
          dot={false}
          name="Metered Consumption"
        />
        <Line 
          type="monotone" 
          dataKey="minimumNightFlow" 
          stroke="#dc2626" 
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="Min Night Flow"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

interface MiniSparklineProps {
  data: number[]
  color?: string
  width?: number
  height?: number
}

export function MiniSparkline({ data, color = '#1e40af', width = 80, height = 24 }: MiniSparklineProps) {
  const chartData = data.map((value, i) => ({ idx: i, value }))
  
  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={chartData}>
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke={color} 
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
