import { useEffect, useState } from 'react'

const statusColour = { active: '#38a169', discharged: '#718096' }

export default function PatientList({ onSelect, apiBase }) {
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${apiBase}/patients`)
      .then(r => r.json())
      .then(data => { setPatients(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ padding: 24 }}>Loading patients…</p>

  return (
    <div>
      <h2 style={{ marginBottom: 20, fontSize: 20, color: '#2d3748' }}>Inpatients</h2>
      <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))' }}>
        {patients.map(p => {
          const enc = p.activeEncounter
          const status = enc?.status || 'unknown'
          return (
            <div key={p.id} onClick={() => onSelect(p.id)} style={{
              background: 'white', borderRadius: 10, padding: 20,
              boxShadow: '0 1px 4px rgba(0,0,0,0.1)', cursor: 'pointer',
              border: '2px solid transparent', transition: 'border-color 0.15s',
            }}
              onMouseEnter={e => e.currentTarget.style.borderColor = '#4299e1'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'transparent'}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 17 }}>{p.name.given} {p.name.family}</span>
                <span style={{
                  background: statusColour[status] || '#718096', color: 'white',
                  padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600
                }}>{status}</span>
              </div>
              <div style={{ color: '#718096', fontSize: 13, marginBottom: 4 }}>
                MRN: {p.mrn} &nbsp;|&nbsp; DOB: {p.birthDate} &nbsp;|&nbsp; {p.gender}
              </div>
              {enc && (
                <div style={{ marginTop: 10, padding: '8px 12px', background: '#ebf8ff', borderRadius: 6, fontSize: 13 }}>
                  <strong>Dx:</strong> {enc.primaryDiagnosis}<br />
                  <strong>Admitted:</strong> {new Date(enc.admissionDate).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })}
                </div>
              )}
              {p.allergies?.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {p.allergies.map((a, i) => (
                    <span key={i} style={{
                      background: '#fff5f5', color: '#c53030', border: '1px solid #feb2b2',
                      padding: '1px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600
                    }}>⚠ {a.substance}</span>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
