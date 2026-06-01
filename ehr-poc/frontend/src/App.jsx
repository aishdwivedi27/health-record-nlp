import { useState } from 'react'
import PatientList from './pages/PatientList.jsx'
import PatientDetail from './pages/PatientDetail.jsx'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [selectedPatientId, setSelectedPatientId] = useState(null)

  return (
    <div style={{ minHeight: '100vh', background: '#f0f4f8' }}>
      <header style={{
        background: '#1a365d', color: 'white', padding: '12px 24px',
        display: 'flex', alignItems: 'center', gap: 16, boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
      }}>
        <span style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>
          🏥 Synthetic EHR PoC
        </span>
        {selectedPatientId && (
          <button onClick={() => setSelectedPatientId(null)} style={{
            background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white',
            padding: '6px 14px', borderRadius: 6, fontSize: 13, marginLeft: 'auto'
          }}>
            ← Patient list
          </button>
        )}
      </header>
      <main style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
        {selectedPatientId
          ? <PatientDetail patientId={selectedPatientId} apiBase={API} />
          : <PatientList onSelect={setSelectedPatientId} apiBase={API} />
        }
      </main>
    </div>
  )
}
