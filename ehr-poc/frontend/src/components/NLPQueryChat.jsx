import { useState, useRef, useEffect } from 'react'

export default function NLPQueryChat({ patientId, apiBase }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'assistant',
      text: 'Hi! I can help you find patient information. Ask me questions like:\n• "What are the latest blood reports?"\n• "Show me active medications"\n• "Compare the last 2 blood reports"\n• "Summarize recent clinical notes"',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedMessageId, setExpandedMessageId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!inputValue.trim()) return

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      // Call NLP query endpoint
      const response = await fetch(`${apiBase}/ai/nlp/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          question: inputValue
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()

      // Add assistant response
      const assistantMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        text: data.narrative_summary,
        structuredData: data.structured_data,
        intent: data.intent,
        executionTime: data.execution_time_ms,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage = {
        id: Date.now().toString(),
        type: 'error',
        text: `Error: ${error.message}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const renderStructuredData = (data) => {
    if (!data || !data.data) return null

    const renderDiagnosticReports = (reports) => (
      <div style={{ marginTop: 12 }}>
        <h4 style={{ margin: '8px 0 4px', fontSize: 12, fontWeight: 600, color: '#2d3748' }}>
          📋 Reports
        </h4>
        {reports.map((report, idx) => (
          <div
            key={idx}
            style={{
              background: '#f7fafc',
              border: '1px solid #e2e8f0',
              borderRadius: 6,
              padding: 10,
              marginTop: 8,
              fontSize: 12
            }}
          >
            <div style={{ fontWeight: 600, color: '#2d3748' }}>{report.type}</div>
            <div style={{ color: '#718096', fontSize: 11, marginTop: 2 }}>
              {new Date(report.timestamp).toLocaleDateString()} {new Date(report.timestamp).toLocaleTimeString()}
            </div>
            {report.findings && (
              <div style={{ marginTop: 6, color: '#4a5568' }}>
                <strong>Findings:</strong> {report.findings}
              </div>
            )}
            {report.conclusion && (
              <div style={{ marginTop: 4, color: '#4a5568' }}>
                <strong>Conclusion:</strong> {report.conclusion}
              </div>
            )}
            <div style={{ marginTop: 6, fontSize: 11, color: '#a0aec0' }}>
              Status: {report.status}
            </div>
          </div>
        ))}
      </div>
    )

    const renderMedications = (meds) => (
      <div style={{ marginTop: 12 }}>
        <h4 style={{ margin: '8px 0 4px', fontSize: 12, fontWeight: 600, color: '#2d3748' }}>
          💊 Medications
        </h4>
        {meds.active && meds.active.length > 0 && (
          <div>
            <div style={{ fontWeight: 600, fontSize: 12, color: '#22543d', marginTop: 6 }}>
              Active ({meds.active.length})
            </div>
            {meds.active.map((med, idx) => (
              <div
                key={`active-${idx}`}
                style={{
                  background: '#f0fdf4',
                  border: '1px solid #bbf7d0',
                  borderRadius: 6,
                  padding: 8,
                  marginTop: 6,
                  fontSize: 12
                }}
              >
                <div style={{ fontWeight: 600, color: '#15803d' }}>{med.name}</div>
                <div style={{ color: '#4a5568', fontSize: 11, marginTop: 4 }}>
                  {med.dose} {med.route} • {med.frequency}
                </div>
                {med.indication && (
                  <div style={{ color: '#4a5568', fontSize: 11, marginTop: 2 }}>
                    Indication: {med.indication}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {meds.inactive && meds.inactive.length > 0 && (
          <div>
            <div style={{ fontWeight: 600, fontSize: 12, color: '#7c2d12', marginTop: 8 }}>
              Inactive ({meds.inactive.length})
            </div>
            {meds.inactive.map((med, idx) => (
              <div
                key={`inactive-${idx}`}
                style={{
                  background: '#fef2f2',
                  border: '1px solid #fecaca',
                  borderRadius: 6,
                  padding: 8,
                  marginTop: 6,
                  fontSize: 12,
                  opacity: 0.8
                }}
              >
                <div style={{ fontWeight: 600, color: '#9a3412' }}>{med.name}</div>
                <div style={{ color: '#4a5568', fontSize: 11, marginTop: 4 }}>
                  {med.dose} {med.route} • {med.frequency}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )

    const renderObservations = (obs) => (
      <div style={{ marginTop: 12 }}>
        <h4 style={{ margin: '8px 0 4px', fontSize: 12, fontWeight: 600, color: '#2d3748' }}>
          📊 Observations
        </h4>
        {obs.map((observation, idx) => (
          <div
            key={idx}
            style={{
              background: '#f0f4f8',
              border: '1px solid #cbd5e0',
              borderRadius: 6,
              padding: 10,
              marginTop: 8,
              fontSize: 12
            }}
          >
            <div style={{ fontWeight: 600, color: '#2d3748' }}>{observation.display}</div>
            <div style={{ color: '#4a5568', marginTop: 4 }}>
              <strong>{observation.value}</strong> {observation.unit}
            </div>
            <div style={{ color: '#718096', fontSize: 11, marginTop: 2 }}>
              {new Date(observation.timestamp).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>
    )

    const renderClinicalNotes = (notes) => (
      <div style={{ marginTop: 12 }}>
        <h4 style={{ margin: '8px 0 4px', fontSize: 12, fontWeight: 600, color: '#2d3748' }}>
          📝 Clinical Notes
        </h4>
        {notes.map((note, idx) => (
          <div
            key={idx}
            style={{
              background: '#f0f4f8',
              border: '1px solid #cbd5e0',
              borderRadius: 6,
              padding: 10,
              marginTop: 8,
              fontSize: 12
            }}
          >
            <div style={{ fontWeight: 600, color: '#2d3748' }}>{note.type}</div>
            <div style={{ color: '#718096', fontSize: 11, marginTop: 2 }}>
              {note.author} • {new Date(note.timestamp).toLocaleDateString()}
            </div>
            <div style={{ marginTop: 6, color: '#4a5568', lineHeight: 1.4 }}>
              {note.content.substring(0, 200)}
              {note.content.length > 200 ? '...' : ''}
            </div>
          </div>
        ))}
      </div>
    )

    // Render based on data type
    if (data.diagnostic_reports) {
      return renderDiagnosticReports(data.diagnostic_reports)
    }
    if (data.lab_observations) {
      return (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ margin: '8px 0 4px', fontSize: 12, fontWeight: 600, color: '#2d3748' }}>
            🧪 Lab Results
          </h4>
          {data.lab_observations.map((obs, idx) => (
            <div
              key={idx}
              style={{
                background: '#f0f4f8',
                border: '1px solid #cbd5e0',
                borderRadius: 6,
                padding: 10,
                marginTop: 8,
                fontSize: 12
              }}
            >
              <div style={{ fontWeight: 600, color: '#2d3748' }}>{obs.test_name}</div>
              <div style={{ color: '#4a5568', marginTop: 4, fontSize: 13, fontWeight: 600 }}>
                {obs.value} {obs.unit}
              </div>
              <div style={{ color: '#718096', fontSize: 11, marginTop: 2 }}>
                {new Date(obs.timestamp).toLocaleDateString()} {new Date(obs.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )
    }
    if (data.medications) {
      return renderMedications(data.medications)
    }
    if (data.observations) {
      return renderObservations(data.observations)
    }
    if (data.clinical_notes) {
      return renderClinicalNotes(data.clinical_notes)
    }

    return null
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'white',
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        <span style={{ fontSize: 20 }}>🤖</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14 }}>EHR Assistant</div>
          <div style={{ fontSize: 12, opacity: 0.8 }}>Natural Language Queries</div>
        </div>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          background: '#f8f9fa'
        }}
      >
        {messages.map(message => (
          <div
            key={message.id}
            style={{
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                background:
                  message.type === 'user'
                    ? '#667eea'
                    : message.type === 'error'
                    ? '#fed7d7'
                    : 'white',
                color:
                  message.type === 'user'
                    ? 'white'
                    : message.type === 'error'
                    ? '#c53030'
                    : '#2d3748',
                padding: '12px 14px',
                borderRadius: message.type === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                border:
                  message.type === 'error'
                    ? '1px solid #fc8181'
                    : message.type !== 'user'
                    ? '1px solid #e2e8f0'
                    : 'none',
                fontSize: 13,
                lineHeight: 1.5,
                wordWrap: 'break-word'
              }}
            >
              <div style={{ whiteSpace: 'pre-wrap' }}>{message.text}</div>

              {/* Structured Data Display */}
              {message.structuredData && (
                <button
                  onClick={() =>
                    setExpandedMessageId(
                      expandedMessageId === message.id ? null : message.id
                    )
                  }
                  style={{
                    marginTop: 10,
                    background: 'rgba(0,0,0,0.05)',
                    border: 'none',
                    color: '#667eea',
                    padding: '6px 10px',
                    borderRadius: 4,
                    fontSize: 12,
                    cursor: 'pointer',
                    fontWeight: 500
                  }}
                >
                  {expandedMessageId === message.id
                    ? '▼ Hide Details'
                    : '▶ Show Details'}
                </button>
              )}

              {expandedMessageId === message.id && message.structuredData && (
                <div style={{ marginTop: 12 }}>
                  {renderStructuredData(message.structuredData)}
                  {message.executionTime && (
                    <div
                      style={{
                        marginTop: 12,
                        paddingTop: 8,
                        borderTop: '1px solid rgba(0,0,0,0.1)',
                        fontSize: 11,
                        color: '#718096'
                      }}
                    >
                      ⚡ Query executed in {message.executionTime.toFixed(0)}ms
                    </div>
                  )}
                </div>
              )}

              <div
                style={{
                  fontSize: 11,
                  opacity: 0.7,
                  marginTop: 6
                }}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                background: 'white',
                border: '1px solid #e2e8f0',
                padding: '12px 14px',
                borderRadius: '12px 12px 12px 0',
                display: 'flex',
                gap: 6,
                alignItems: 'center'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  gap: 4
                }}
              >
                {[0, 1, 2].map(i => (
                  <div
                    key={i}
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: '#667eea',
                      animation: `pulse 1.4s infinite`,
                      animationDelay: `${i * 0.2}s`
                    }}
                  />
                ))}
              </div>
              <span style={{ fontSize: 12, color: '#718096', marginLeft: 6 }}>
                Querying EHR...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          gap: 8,
          padding: '12px 16px',
          background: 'white',
          borderTop: '1px solid #e2e8f0'
        }}
      >
        <input
          type="text"
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          placeholder="Ask about this patient's records..."
          disabled={loading}
          style={{
            flex: 1,
            border: '1px solid #cbd5e0',
            borderRadius: 6,
            padding: '10px 12px',
            fontSize: 13,
            fontFamily: 'inherit',
            outline: 'none',
            transition: 'border-color 0.2s'
          }}
          onFocus={e => (e.target.style.borderColor = '#667eea')}
          onBlur={e => (e.target.style.borderColor = '#cbd5e0')}
        />
        <button
          type="submit"
          disabled={loading || !inputValue.trim()}
          style={{
            background: loading || !inputValue.trim() ? '#cbd5e0' : '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            padding: '10px 16px',
            fontSize: 13,
            fontWeight: 600,
            cursor: loading || !inputValue.trim() ? 'not-allowed' : 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={e => {
            if (!loading && inputValue.trim()) {
              e.target.style.background = '#5a67d8'
            }
          }}
          onMouseLeave={e => {
            if (!loading && inputValue.trim()) {
              e.target.style.background = '#667eea'
            }
          }}
        >
          Send
        </button>
      </form>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  )
}
