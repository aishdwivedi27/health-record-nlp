# EHR NLP Assistant - Architecture & System Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              NLPQueryChat Component                        │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Chat Interface                                       │  │ │
│  │  │  - User asks question in natural language            │  │ │
│  │  │  - Displays narrative summary                        │  │ │
│  │  │  - Shows expandable structured data                  │  │ │
│  │  │  - Real-time streaming messages                      │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    HTTP POST /ai/nlp/query
                    {patient_id, question}
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI + Python)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         /ai/nlp/query Endpoint (nlp_query.py)           │  │
│  │                                                           │  │
│  │  Step 1: Intent Extraction                              │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Claude API: extract_intent()                       │ │  │
│  │  │ Input: "What are the latest blood reports?"       │ │  │
│  │  │ Output: {                                          │ │  │
│  │  │   primary_data_type: "diagnostic_report",         │ │  │
│  │  │   action: "latest",                               │ │  │
│  │  │   report_type: "blood",                           │ │  │
│  │  │   time_range: {days_back: 30},                    │ │  │
│  │  │   confidence: 0.95                                │ │  │
│  │  │ }                                                  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  Step 2: Execute Query                                  │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ execute_query() → Database Query Execution         │ │  │
│  │  │                                                    │ │  │
│  │  │ Query Logic:                                       │ │  │
│  │  │  if data_type == "diagnostic_report":            │ │  │
│  │  │    - Filter by patient_id                         │ │  │
│  │  │    - Filter by report_type                        │ │  │
│  │  │    - Order by timestamp DESC                      │ │  │
│  │  │    - Limit results based on action                │ │  │
│  │  │    - Return: {findings, conclusion, status}       │ │  │
│  │  │                                                    │ │  │
│  │  │  if data_type == "medication":                    │ │  │
│  │  │    - Filter by patient_id                         │ │  │
│  │  │    - Group by status (active/inactive)            │ │  │
│  │  │    - Return: {name, dose, frequency, status}      │ │  │
│  │  │                                                    │ │  │
│  │  │  if data_type == "observation":                   │ │  │
│  │  │    - Filter by patient_id & type                  │ │  │
│  │  │    - Get latest of each type                      │ │  │
│  │  │    - Return: {type, value, unit, timestamp}       │ │  │
│  │  │                                                    │ │  │
│  │  │  ... (similar for clinical_note, procedure)       │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  Step 3: Generate Narrative Summary                      │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │ Claude API: generate_narrative_summary()          │ │  │
│  │  │ Input: {question, structured_data, intent}        │ │  │
│  │  │ Output: "The patient has a recent blood panel...  │ │  │
│  │  │          showing elevated glucose..."             │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  Return Response:                                        │  │
│  │  {                                                        │  │
│  │    intent: {...extracted intent...},                    │  │
│  │    structured_data: {...database results...},           │  │
│  │    narrative_summary: "...natural language...",         │  │
│  │    execution_time_ms: 1234.5                           │  │
│  │  }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Database Layer (SQLAlchemy ORM)                          │ │
│  │  - Patient, Encounter, Observation                        │ │
│  │  - Medication, DiagnosticReport                           │ │
│  │  - ClinicalNote, Procedure, DischargeSummary             │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
    ┌───────────▼──────────┐    ┌────────────▼──────────┐
    │  Claude API (Remote) │    │  Database (SQLite)    │
    │  - Intent extraction │    │  - EHR data storage   │
    │  - Text generation   │    │  - Patient records    │
    │  ~500-1500ms/call    │    │  - <100ms queries     │
    └──────────────────────┘    └───────────────────────┘
```

## Data Flow - Complete Example

### Request
```
User Question: "Compare the last 2 blood reports"
Patient ID: "patient-123"
```

### Processing Flow

**1. Intent Extraction (500-1500ms)**
```python
# User's question sent to Claude
prompt = """
Question: "Compare the last 2 blood reports"
...extract intent JSON...
"""

# Claude returns:
{
  "primary_data_type": "diagnostic_report",
  "action": "compare",
  "report_type": "blood",
  "time_range": {"comparison_count": 2}
}
```

**2. Database Query Execution (<100ms)**
```python
# Using extracted intent to build optimized query
query = db.query(DiagnosticReport)\
  .filter(
    DiagnosticReport.patient_id == "patient-123",
    DiagnosticReport.category.ilike("%blood%")
  )\
  .order_by(DiagnosticReport.timestamp.desc())\
  .limit(2)

# Returns:
[
  {
    "id": "report-1",
    "timestamp": "2024-01-15T10:30:00",
    "type": "Blood Panel",
    "findings": "Elevated glucose: 145 mg/dL",
    "conclusion": "Pre-diabetic state"
  },
  {
    "id": "report-2",
    "timestamp": "2024-01-08T09:15:00",
    "type": "Blood Panel",
    "findings": "Elevated glucose: 138 mg/dL",
    "conclusion": "Borderline high glucose"
  }
]
```

**3. Narrative Generation (500-1500ms)**
```python
# Structured data + question sent back to Claude
prompt = """
Question: "Compare the last 2 blood reports"
Structured Data: [...reports...]
Generate a clinical summary comparing these reports.
"""

# Claude returns:
"The patient had two blood panels 7 days apart. 
The glucose level increased from 138 to 145 mg/dL, 
indicating a worsening trend. Both readings are 
elevated and warrant dietary intervention. 
Consider follow-up testing in 2 weeks."
```

### Response
```json
{
  "intent": {
    "primary_data_type": "diagnostic_report",
    "action": "compare",
    "report_type": "blood",
    "confidence": 0.98
  },
  "structured_data": {
    "diagnostic_reports": [
      {
        "timestamp": "2024-01-15T10:30:00",
        "findings": "Elevated glucose: 145 mg/dL",
        "conclusion": "Pre-diabetic state"
      },
      {
        "timestamp": "2024-01-08T09:15:00",
        "findings": "Elevated glucose: 138 mg/dL",
        "conclusion": "Borderline high glucose"
      }
    ]
  },
  "narrative_summary": "The patient had two blood panels...",
  "execution_time_ms": 2345.6
}
```

## Why Hybrid Approach?

### ❌ Rule-Based Only
- Limited flexibility
- Can't handle variations ("latest imaging" vs "most recent scan")
- Many false negatives
- High maintenance as EHR grows

### ❌ Claude Only
- Slow (2-3 seconds per query)
- Expensive ($0.05+ per query)
- May generate inaccurate data without structure

### ✅ Hybrid (What We Use)
1. **Claude**: Understands intent (smart, flexible)
2. **Database**: Executes optimized queries (fast, accurate)
3. **Claude**: Summarizes results (natural language)

**Benefits:**
- Fast: Total ~2-3 seconds
- Accurate: Database ensures data correctness
- Flexible: Claude handles natural language variations
- Cost-effective: Structured queries reduce API calls

## Supported Query Patterns

### Diagnostic Reports
```
- "Latest blood report"
- "Show me the most recent X-ray"
- "Compare last 3 CT scans"
- "Any imaging in the past 3 months?"
- "What's the latest lab result?"
```

### Medications
```
- "What medications is patient on?"
- "Active medications with dosages"
- "Closed medications and when"
- "What was the patient taking?"
- "Current drug regimen"
```

### Vitals & Observations
```
- "Latest vital signs"
- "Temperature trend this week"
- "Recent blood pressure readings"
- "What are current lab values?"
```

### Clinical Notes
```
- "Summarize the notes"
- "Latest progress note"
- "What was documented?"
- "Recent clinical assessment"
```

### Procedures
```
- "What procedures were done?"
- "Latest surgery"
- "Recent interventions"
```

## Performance Characteristics

| Component | Time | Notes |
|-----------|------|-------|
| Intent Extraction (Claude) | 500-1500ms | API latency varies |
| Database Query | <100ms | Optimized by intent |
| Narrative Generation (Claude) | 500-1500ms | Depends on data size |
| **Total** | **1-3 seconds** | Typical response time |

## Scalability Considerations

### Current Limits
- Single patient focus
- 90-day default lookback
- Max 50 records per query
- One request at a time

### To Scale
1. **Add Caching**: Cache common queries
2. **Pagination**: Support "next 10 results"
3. **Async Processing**: Use background jobs for heavy summaries
4. **Multi-patient**: Support "compare patients"
5. **Batch Queries**: Process multiple patients simultaneously

## Security & Privacy

1. **Patient Isolation**: All queries filtered by patient_id
2. **No Data Retention**: Claude doesn't store conversations
3. **API Key Protection**: Never in code/logs
4. **Audit Trail**: Log all queries (in production)

## Integration Points

### With Existing EHR-POC
- Uses existing database
- Compatible with FHIR endpoints
- Works with seed data
- Extends without modifying existing tables

### Frontend Integration
- New "AI Assistant" tab in PatientDetail
- Uses same styling as other components
- No disruption to existing features
- Backward compatible

## Model Selection

### Claude Opus 4.1 (Current)
- Most capable model
- Best at understanding complex queries
- Highest cost (~$0.003 input, $0.015 output per 1K tokens)
- Recommended for complex EHR data

### Alternatives
```python
# Faster, cheaper (but less capable)
model="claude-3-sonnet"

# Fastest, cheapest (basic capabilities)
model="claude-3-haiku"
```

## Cost Estimation

### Per Query Costs (Opus 4.1)
- Intent extraction: ~$0.0003-0.0005
- Narrative generation: ~$0.001-0.003
- **Total: ~$0.002-0.004 per query**

### Monthly Estimate (100 patients, 5 queries/day)
- 500 queries/day × 30 days = 15,000 queries
- 15,000 × $0.003 = **~$45/month**

## Future Enhancements

1. **Context Memory**: Remember previous questions
2. **Predictive Alerts**: "Patient showing diabetes trend"
3. **Report Generation**: Auto-generate clinical letters
4. **Multi-patient Queries**: Compare across patients
5. **Voice Interface**: Speak questions instead of typing
6. **Integration with Orders**: "Order a repeat X-ray based on findings"

## Troubleshooting Guide

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| Slow responses | Claude API latency | Normal, expected 1-3s |
| Wrong patient data | Wrong patient_id | Verify ID in request |
| Generic answers | Low confidence intent | Ask more specifically |
| API errors | Rate limiting | Implement backoff |
| Missing data | Time range too narrow | Increase days_back |

---

**Last Updated**: January 2024
**Version**: 1.0
**Status**: Production Ready ✅
