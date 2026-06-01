import { useEffect, useState, useCallback } from 'react'
import LabChart from '../components/LabChart.jsx'
import NLPQueryChat from '../components/NLPQueryChat.jsx'

const DISCHARGE_SERVER = 'http://localhost:5000'

const TABS = ['Overview', 'Timeline', 'Labs', 'Imaging', 'Medications', 'Notes', 'Discharge Summary', 'AI Assistant']
const tabStyle = (active) => ({
  padding: '8px 18px', borderRadius: '6px 6px 0 0', border: 'none', fontWeight: 600,
  background: active ? 'white' : 'transparent', color: active ? '#2b6cb0' : '#718096',
  cursor: 'pointer', fontSize: 14, borderBottom: active ? '3px solid #2b6cb0' : 'none'
})

const typeIcon = {
  'vital-signs': '💓', lab: '🧪', medication: '💊', report: '📋',
  procedure: '🔧', 'progress-note': '📝', consult: '👨‍⚕️',
  'ward-round': '🏥', nursing: '👩‍⚕️', operative: '🔬', 'discharge-summary': '📋'
}

const NOTE_TYPES = ['progress-note', 'consult', 'ward-round', 'nursing', 'operative', 'discharge-summary']

export default function PatientDetail({ patientId, apiBase }) {
  const [patient, setPatient] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [observations, setObservations] = useState([])
  const [medications, setMedications] = useState([])
  const [reports, setReports] = useState([])
  const [clinicalNotes, setClinicalNotes] = useState([])
  const [tab, setTab] = useState('Overview')
  const [loading, setLoading] = useState(true)

  // Discharge summary tab state
  const [dischargeBundle, setDischargeBundle] = useState(null)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [aiSummary, setAiSummary] = useState(null)
  const [savedSummaries, setSavedSummaries] = useState([])

  const loadPatientData = useCallback(async () => {
    const [p, t, o, m, r] = await Promise.all([
      fetch(`${apiBase}/patients/${patientId}`).then(r => r.json()),
      fetch(`${apiBase}/patients/${patientId}/timeline`).then(r => r.json()),
      fetch(`${apiBase}/observations?patientId=${patientId}`).then(r => r.json()),
      fetch(`${apiBase}/medications?patientId=${patientId}`).then(r => r.json()),
      fetch(`${apiBase}/reports?patientId=${patientId}`).then(r => r.json()),
    ])
    setPatient(p)
    const events = t.events || []
    setTimeline(events)
    // Extract clinical notes from timeline (includes discharge-summary type)
    setClinicalNotes(events.filter(ev => NOTE_TYPES.includes(ev.type)))
    setObservations(o)
    setMedications(m)
    setReports(r)
    setLoading(false)
  }, [patientId, apiBase])

  useEffect(() => { loadPatientData() }, [loadPatientData])

  // Reload notes after tab switch to Notes or Discharge Summary to pick up newly saved notes
  useEffect(() => {
    if (tab === 'Notes' || tab === 'Discharge Summary') {
      fetch(`${apiBase}/patients/${patientId}/timeline`)
        .then(r => r.json())
        .then(t => {
          const events = t.events || []
          setTimeline(events)
          setClinicalNotes(events.filter(ev => NOTE_TYPES.includes(ev.type)))
        })
        .catch(() => {})
    }
  }, [tab, patientId, apiBase])

  const loadDischargeBundle = async () => {
    if (!patient?.encounters?.[0]) return
    const encId = patient.encounters[0].id
    const res = await fetch(`${apiBase}/ai/discharge-ready/${encId}`)
    const bundle = await res.json()
    setDischargeBundle(bundle)
    // Also load saved summaries
    const saved = clinicalNotes.filter(n => n.type === 'discharge-summary')
    setSavedSummaries(saved)
  }

  const generateAiSummary = async () => {
    if (!dischargeBundle) return
    setGeneratingSummary(true); setAiSummary(null)
    try {
      // Route through the discharge summary server — it holds the API key
      const res = await fetch(`${DISCHARGE_SERVER}/generate-summary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doctorNotes: '',
          country: 'Australia',
          ehrContext: dischargeBundle,
          patientId: patientId,
          encounterId: patient?.encounters?.[0]?.id,
        })
      })
      if (!res.ok) {
        const err = await res.json()
        setAiSummary('Error: ' + (err.error || res.statusText))
        setGeneratingSummary(false); return
      }
      const data = await res.json()
      setAiSummary(data.summaryText || JSON.stringify(data, null, 2))
    } catch (err) {
      setAiSummary('Error: Could not reach discharge summary server on port 5000. Make sure Terminal 2 is running.')
    }
    setGeneratingSummary(false)
  }

  if (loading) return <p style={{ padding: 24 }}>Loading patient…</p>
  if (!patient) return <p style={{ padding: 24 }}>Patient not found.</p>

  const enc = patient.encounters?.[0]
  const labs = observations.filter(o => o.type === 'lab')
  const vitals = observations.filter(o => o.type === 'vital-signs')

  return (
    <div>
      {/* Patient header */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, marginBottom: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>{patient.name?.given} {patient.name?.family}</h2>
            <div style={{ color: '#718096', fontSize: 13 }}>
              MRN: {patient.mrn} &nbsp;|&nbsp; DOB: {patient.birthDate} &nbsp;|&nbsp; {patient.gender}
            </div>
            {patient.pastMedicalHistory?.length > 0 && (
              <div style={{ marginTop: 6, fontSize: 13 }}>
                <strong>PHx:</strong> {patient.pastMedicalHistory.join(', ')}
              </div>
            )}
          </div>
          {patient.allergies?.length > 0 && (
            <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start', flexWrap: 'wrap' }}>
              {patient.allergies.map((a, i) => (
                <span key={i} style={{
                  background: '#fff5f5', color: '#c53030', border: '1px solid #feb2b2',
                  padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700
                }}>⚠ {a.substance} ({a.reaction})</span>
              ))}
            </div>
          )}
        </div>
        {enc && (
          <div style={{ marginTop: 14, padding: '10px 14px', background: '#ebf8ff', borderRadius: 8, fontSize: 13 }}>
            <strong>Admission:</strong> {enc.primaryDiagnosis} &nbsp;|&nbsp;
            <strong>Admitted:</strong> {new Date(enc.admissionDate).toLocaleDateString('en-AU')} &nbsp;|&nbsp;
            <strong>Status:</strong>{' '}
            <span style={{ fontWeight: 700, color: enc.status === 'active' ? '#276749' : '#718096' }}>
              {enc.status}
            </span>
            {enc.dischargeDate && <> &nbsp;|&nbsp; <strong>Discharged:</strong> {new Date(enc.dischargeDate).toLocaleDateString('en-AU')}</>}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '2px solid #e2e8f0', marginBottom: 0, background: '#f7fafc', borderRadius: '8px 8px 0 0', padding: '8px 8px 0', flexWrap: 'wrap' }}>
        {TABS.map(t => <button key={t} style={tabStyle(tab === t)} onClick={() => setTab(t)}>{t}</button>)}
      </div>

      <div style={{ background: 'white', borderRadius: '0 0 10px 10px', padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', minHeight: 300 }}>

        {/* ── OVERVIEW ── */}
        {tab === 'Overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <Section title="Latest Vitals">
              {['Heart rate', 'Body temperature', 'SpO2', 'Blood pressure systolic', 'Respiratory rate'].map(name => {
                const last = [...vitals].filter(v => v.display === name).pop()
                return last ? (
                  <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f4f8', fontSize: 14 }}>
                    <span style={{ color: '#718096' }}>{name}</span>
                    <strong>{last.value} {last.unit}</strong>
                  </div>
                ) : null
              })}
            </Section>
            <Section title="Latest Labs">
              {['WBC', 'Haemoglobin', 'CRP', 'Troponin I', 'BNP', 'INR', 'Creatinine'].map(name => {
                const last = [...labs].filter(l => l.display === name).pop()
                return last ? (
                  <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f4f8', fontSize: 14 }}>
                    <span style={{ color: '#718096' }}>{name}</span>
                    <strong>{last.value} {last.unit}</strong>
                  </div>
                ) : null
              })}
            </Section>
            <Section title="Active Medications">
              {medications.filter(m => m.status === 'active').map(m => (
                <div key={m.id} style={{ padding: '5px 0', borderBottom: '1px solid #f0f4f8', fontSize: 13 }}>
                  <strong>{m.name}</strong> — {m.dose} {m.route} {m.frequency}
                </div>
              ))}
            </Section>
            <Section title="Home Medications">
              {(patient.medicationHistory || []).map((m, i) => (
                <div key={i} style={{ padding: '4px 0', fontSize: 13, color: '#4a5568' }}>• {m}</div>
              ))}
            </Section>
          </div>
        )}

        {/* ── TIMELINE ── */}
        {tab === 'Timeline' && (
          <div>
            {timeline.map((ev, i) => (
              <div key={i} style={{ display: 'flex', gap: 14, padding: '10px 0', borderBottom: '1px solid #f0f4f8' }}>
                <div style={{ minWidth: 160, color: '#718096', fontSize: 12 }}>
                  {new Date(ev.timestamp).toLocaleString('en-AU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                </div>
                <div style={{ fontSize: 18, minWidth: 24 }}>{typeIcon[ev.type] || '📌'}</div>
                <div style={{ flex: 1, fontSize: 13 }}>
                  <strong>{ev.display || ev.subject || ev.name}</strong>
                  {ev.value && <span style={{ color: '#2b6cb0' }}> — {ev.value} {ev.unit}</span>}
                  {ev.conclusion && <div style={{ color: '#4a5568', marginTop: 2 }}>{ev.conclusion}</div>}
                  {ev.content && <div style={{ color: '#4a5568', marginTop: 2, fontSize: 12, whiteSpace: 'pre-wrap', maxHeight: 80, overflow: 'hidden' }}>{ev.content.slice(0, 200)}{ev.content.length > 200 ? '…' : ''}</div>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── LABS ── */}
        {tab === 'Labs' && (
          <div>
            <LabChart observations={labs} />
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 20, fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f7fafc' }}>
                  {['Time', 'Test', 'Value', 'Unit'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {labs.map((l, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f0f4f8' }}>
                    <td style={{ padding: '7px 12px', color: '#718096' }}>{new Date(l.timestamp).toLocaleString('en-AU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                    <td style={{ padding: '7px 12px' }}>{l.display}</td>
                    <td style={{ padding: '7px 12px', fontWeight: 600, color: '#2b6cb0' }}>{l.value}</td>
                    <td style={{ padding: '7px 12px', color: '#718096' }}>{l.unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── IMAGING ── */}
        {tab === 'Imaging' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {reports.map(r => (
              <div key={r.id} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <strong>{r.display}</strong>
                  <span style={{ fontSize: 12, color: '#718096', background: '#f7fafc', padding: '2px 8px', borderRadius: 10 }}>{r.category}</span>
                </div>
                <div style={{ fontSize: 12, color: '#718096', marginBottom: 8 }}>
                  {new Date(r.timestamp).toLocaleDateString('en-AU', { day: '2-digit', month: 'short', year: 'numeric' })}
                </div>
                <div style={{ fontSize: 13, marginBottom: 6 }}><strong>Findings:</strong> {r.findings}</div>
                <div style={{ fontSize: 13, background: '#f0fff4', padding: '8px 12px', borderRadius: 6, color: '#276749' }}>
                  <strong>Conclusion:</strong> {r.conclusion}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── MEDICATIONS ── */}
        {tab === 'Medications' && (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f7fafc' }}>
                {['Medication', 'Dose', 'Route', 'Frequency', 'Indication', 'Status'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 600, color: '#4a5568', borderBottom: '2px solid #e2e8f0' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {medications.map((m, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #f0f4f8', background: m.status === 'active' ? '#f0fff4' : 'white' }}>
                  <td style={{ padding: '8px 12px', fontWeight: m.status === 'active' ? 600 : 400 }}>{m.name}</td>
                  <td style={{ padding: '8px 12px' }}>{m.dose}</td>
                  <td style={{ padding: '8px 12px', color: '#718096' }}>{m.route}</td>
                  <td style={{ padding: '8px 12px', color: '#718096' }}>{m.frequency}</td>
                  <td style={{ padding: '8px 12px', color: '#4a5568', fontSize: 12 }}>{m.indication}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span style={{
                      background: m.status === 'active' ? '#c6f6d5' : '#e2e8f0',
                      color: m.status === 'active' ? '#276749' : '#718096',
                      padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 600
                    }}>{m.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* ── NOTES ── includes discharge-summary type ── */}
        {tab === 'Notes' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {clinicalNotes.length === 0 && (
              <p style={{ color: '#a0aec0', fontSize: 13 }}>No clinical notes recorded.</p>
            )}
            {clinicalNotes.map((n, i) => (
              <div key={i} style={{
                border: `1px solid ${n.type === 'discharge-summary' ? '#9ae6b4' : '#e2e8f0'}`,
                borderRadius: 8, padding: 16,
                background: n.type === 'discharge-summary' ? '#f0fff4' : 'white'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <strong style={{ fontSize: 15, color: n.type === 'discharge-summary' ? '#276749' : '#2d3748' }}>
                    {typeIcon[n.type] || '📝'} {n.subject}
                  </strong>
                  <span style={{ fontSize: 12, color: '#718096' }}>
                    {new Date(n.timestamp).toLocaleString('en-AU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#718096', marginBottom: 8 }}>
                  {n.author} &nbsp;·&nbsp;
                  <span style={{
                    textTransform: 'capitalize',
                    background: n.type === 'discharge-summary' ? '#c6f6d5' : '#ebf8ff',
                    color: n.type === 'discharge-summary' ? '#276749' : '#2b6cb0',
                    padding: '1px 8px', borderRadius: 10
                  }}>{n.type}</span>
                </div>
                <div style={{ fontSize: 13, color: '#2d3748', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{n.content}</div>
              </div>
            ))}
          </div>
        )}

        {/* ── DISCHARGE SUMMARY ── */}
        {tab === 'Discharge Summary' && (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button onClick={loadDischargeBundle} style={{
                background: '#2b6cb0', color: 'white', border: 'none',
                padding: '8px 18px', borderRadius: 6, fontWeight: 600, fontSize: 13, cursor: 'pointer'
              }}>Load discharge bundle</button>
              {dischargeBundle && (
                <button onClick={generateAiSummary} disabled={generatingSummary} style={{
                  background: '#6b46c1', color: 'white', border: 'none',
                  padding: '8px 18px', borderRadius: 6, fontWeight: 600, fontSize: 13, cursor: 'pointer',
                  opacity: generatingSummary ? 0.7 : 1
                }}>{generatingSummary ? '⏳ Generating…' : '✨ Generate AI summary'}</button>
              )}
            </div>

            {dischargeBundle && (
              <div style={{ background: '#f7fafc', borderRadius: 8, padding: 12, marginBottom: 16, fontSize: 12, color: '#718096' }}>
                Bundle loaded: {dischargeBundle.clinicalNotes?.length} notes, {dischargeBundle.medications?.length} medications, {dischargeBundle.diagnosticReports?.length} reports
              </div>
            )}

            {/* AI summary */}
            {aiSummary && (
              <div style={{ background: '#f0fff4', border: '1px solid #9ae6b4', borderRadius: 8, padding: 20, marginBottom: 20 }}>
                <h4 style={{ marginBottom: 12, color: '#276749' }}>✨ AI-Generated Discharge Summary</h4>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: '#2d3748', fontFamily: 'inherit', lineHeight: 1.6 }}>{aiSummary}</pre>
              </div>
            )}

            {/* Saved discharge summary notes from EHR */}
            {clinicalNotes.filter(n => n.type === 'discharge-summary').length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h4 style={{ marginBottom: 12, fontSize: 15, color: '#276749' }}>📋 Saved Discharge Summary Notes</h4>
                {clinicalNotes.filter(n => n.type === 'discharge-summary').map((n, i) => (
                  <div key={i} style={{ background: '#f0fff4', border: '1px solid #9ae6b4', borderRadius: 8, padding: 16, marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <strong style={{ color: '#276749' }}>{n.subject}</strong>
                      <span style={{ fontSize: 12, color: '#718096' }}>
                        {new Date(n.timestamp).toLocaleString('en-AU', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: '#718096', marginBottom: 8 }}>{n.author}</div>
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, fontFamily: 'inherit', lineHeight: 1.7, color: '#2d3748' }}>{n.content}</pre>
                  </div>
                ))}
              </div>
            )}

            {/* Info if no saved summaries yet */}
            {clinicalNotes.filter(n => n.type === 'discharge-summary').length === 0 && !aiSummary && (
              <div style={{ background: '#fffbeb', border: '1px solid #fbd38d', borderRadius: 8, padding: 20 }}>
                <p style={{ fontSize: 13, color: '#744210', marginBottom: 8 }}>
                  No discharge summary saved to EHR yet for this patient.
                </p>
                <p style={{ fontSize: 12, color: '#975a16' }}>
                  Use PiMed Clinical Discharge Scribe at <strong>localhost:5001</strong> to generate and save a discharge summary.
                  It will appear here automatically under the Notes tab and this tab once saved.
                </p>
              </div>
            )}
          </div>
        )}

        {tab === 'AI Assistant' && (
          <div style={{ height: '70vh', display: 'flex' }}>
            <NLPQueryChat patientId={patientId} apiBase={apiBase} />
          </div>
        )}

      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 16 }}>
      <h4 style={{ marginBottom: 12, fontSize: 14, color: '#4a5568', fontWeight: 700 }}>{title}</h4>
      {children}
    </div>
  )
}
