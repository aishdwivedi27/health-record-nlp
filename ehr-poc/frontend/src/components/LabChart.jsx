import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useMemo } from 'react'

const TRACKED = ['WBC', 'CRP', 'Haemoglobin', 'Troponin I', 'BNP', 'INR']
const COLOURS = { WBC: '#3182ce', CRP: '#e53e3e', Haemoglobin: '#805ad5', 'Troponin I': '#d69e2e', BNP: '#38a169', INR: '#dd6b20' }

export default function LabChart({ observations }) {
  const data = useMemo(() => {
    const byTime = {}
    observations.filter(o => TRACKED.includes(o.display)).forEach(o => {
      const label = new Date(o.timestamp).toLocaleString('en-AU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
      if (!byTime[label]) byTime[label] = { time: label }
      byTime[label][o.display] = o.value
    })
    return Object.values(byTime)
  }, [observations])

  const trackedPresent = TRACKED.filter(t => data.some(d => d[t] !== undefined))

  if (!data.length) return null

  return (
    <div style={{ marginBottom: 8 }}>
      <h4 style={{ marginBottom: 12, fontSize: 14, color: '#4a5568', fontWeight: 700 }}>Lab trends</h4>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {trackedPresent.map(name => (
            <Line key={name} type="monotone" dataKey={name} stroke={COLOURS[name]} dot={{ r: 3 }} strokeWidth={2} connectNulls />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
