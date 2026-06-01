# EHR-POC NLP Assistant Setup Guide

## Overview

The NLP Assistant enables doctors to ask natural language questions about patient records and get intelligent responses with both structured data and narrative summaries.

**Examples:**
- "Is there a latest blood report available?"
- "Compare the last 2 blood reports"
- "What active medications are on the patient?"
- "What are the latest vital signs?"
- "Summarize the clinical notes from latest to earliest"

## Architecture

The system uses a **hybrid NLP approach**:

1. **Intent Extraction**: Claude API understands the doctor's natural language query and extracts:
   - What data type (blood report, medications, vitals, notes, etc.)
   - What action (latest, compare, summarize, filter, etc.)
   - Time range and filters
   
2. **Optimized Query Execution**: The system executes database queries based on extracted intent

3. **Narrative Generation**: Claude API generates a natural language summary of the results

4. **Dual Response**: Returns both structured JSON data AND narrative summary

## Prerequisites

### Backend Requirements
- Python 3.10+
- FastAPI 0.115.0+
- SQLAlchemy 2.0+
- Anthropic API key (for Claude)

### Frontend Requirements
- Node.js 16+
- React 18+
- Vite

## Installation

### 1. Backend Setup

#### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

The requirements now include:
- `anthropic==0.28.1` - Claude API client
- `python-dateutil==2.8.2` - Date handling

#### Configure Environment Variables
Create a `.env` file in the backend root:

```env
ANTHROPIC_API_KEY=your-anthropic-api-key-here
DATABASE_URL=sqlite:///./ehr.db
```

**Get your API key:**
1. Visit https://console.anthropic.com
2. Create an API key
3. Add it to `.env`

#### Verify Installation
```bash
python -c "import anthropic; print('Anthropic library installed successfully')"
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

No additional dependencies needed - uses existing React + Vite setup.

## Running the Application

### Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Start Frontend
```bash
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Using the NLP Assistant

### In the UI

1. Navigate to a patient's detail page
2. Click the **"AI Assistant"** tab
3. Type your question in natural language
4. Press Send or click the Send button

### Example Questions

```
Healthcare Questions:
- "Is there a latest blood report available?"
- "Show me the most recent X-ray report"
- "Compare the last 2 blood reports"
- "What active medications does the patient have?"
- "What are the closed medications and their dosages?"
- "What are the patient's latest vital signs?"
- "Summarize the clinical notes from latest to earliest"
- "What procedures have been performed recently?"
- "Show me all lab results from the past month"
- "Is there any imaging available in the last 3 months?"
- "List all current medications with their dosages and frequencies"
- "What was the patient's temperature trend over the last week?"
```

### Supported Query Types

#### 1. Diagnostic Reports (Blood, Xray, Labs, etc.)
- Latest report of a type
- Compare multiple reports
- Filter by date range
- Search by report type

#### 2. Medications
- List active medications with dosages
- List inactive/closed medications
- Show medication details (indication, frequency, route)
- Filter by medication status

#### 3. Observations (Vitals & Labs)
- Latest vital signs
- Specific observation types
- Time-range filtered
- Latest of each type

#### 4. Clinical Notes
- Summarize all notes
- Chronological ordering (latest to earliest)
- Note type filtering
- Author information

#### 5. Procedures
- List recent procedures
- Filter by date range
- Get procedure details

## API Endpoints

### POST `/ai/nlp/query`

Sends a natural language query and returns structured data + narrative.

**Request:**
```json
{
  "patient_id": "abc123",
  "question": "What are the latest blood reports?"
}
```

**Response:**
```json
{
  "patient_id": "abc123",
  "question": "What are the latest blood reports?",
  "intent": {
    "primary_data_type": "diagnostic_report",
    "action": "latest",
    "report_type": "blood",
    "confidence": 0.95
  },
  "structured_data": {
    "patient": {
      "id": "abc123",
      "name": "John Doe",
      "mrn": "MRN12345"
    },
    "data": {
      "diagnostic_reports": [
        {
          "id": "report1",
          "timestamp": "2024-01-15T10:30:00",
          "category": "lab",
          "type": "Blood Panel",
          "findings": "Elevated glucose levels",
          "conclusion": "Results indicate pre-diabetic state",
          "status": "final"
        }
      ]
    },
    "metadata": {
      "data_type": "diagnostic_report",
      "action": "latest",
      "record_count": 1
    }
  },
  "narrative_summary": "The patient has a recent blood panel from January 15, 2024 showing elevated glucose levels, which indicates a pre-diabetic state. This requires monitoring and possible lifestyle modifications.",
  "execution_time_ms": 234.5
}
```

### GET `/ai/nlp/sample-queries`

Returns example questions doctors can ask.

**Response:**
```json
{
  "examples": [
    "Is there a latest blood report available?",
    "What active medications does the patient have?",
    ...
  ]
}
```

## Data Model

The NLP system interacts with these EHR entities:

### DiagnosticReport
- `id`: Unique identifier
- `patient_id`: Associated patient
- `timestamp`: Report date/time
- `category`: Type (lab, imaging, etc.)
- `display`: Human-readable type
- `findings`: What was found
- `conclusion`: Clinical conclusion
- `status`: Report status

### Medication
- `id`: Unique identifier
- `patient_id`: Associated patient
- `name`: Medication name
- `dose`: Dosage amount
- `route`: Administration route
- `frequency`: How often taken
- `indication`: Why prescribed
- `status`: active/inactive
- `timestamp`: When recorded

### Observation
- `id`: Unique identifier
- `patient_id`: Associated patient
- `type`: vital, lab, imaging, etc.
- `display`: Human-readable name
- `value`: Numeric value
- `value_string`: String value
- `unit`: Measurement unit
- `timestamp`: When recorded
- `status`: Status

### ClinicalNote
- `id`: Unique identifier
- `patient_id`: Associated patient
- `type`: Note type
- `author`: Who wrote it
- `subject`: Note subject
- `content`: Full text
- `timestamp`: When written

## Intent Extraction Details

Claude analyzes the question and extracts:

```json
{
  "primary_data_type": "diagnostic_report|medication|observation|clinical_note|procedure",
  "action": "retrieve|compare|summarize|filter|latest",
  "report_type": null or "blood|xray|ct|lab|imaging",
  "medication_status": null or "active|inactive|all",
  "observation_types": null or ["vital", "lab", "imaging"],
  "time_range": {
    "days_back": 30 or 90 or 365,
    "specific_date": "YYYY-MM-DD" or null,
    "comparison_count": 2 or 3 (for comparisons)
  },
  "confidence": 0.0 to 1.0
}
```

## Performance

- Intent extraction: ~500-1500ms (Claude API call)
- Database query: <100ms
- Narrative generation: ~500-1500ms (Claude API call)
- **Total query time: ~1-3 seconds**

For optimal performance:
- Results limited to 90 days by default
- Latest reports limited to 1 record
- Comparison limited to 5 records max

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Ensure `.env` file exists in backend root
- Verify the key format
- Restart the backend server

### "Patient not found"
- Check patient_id is correct
- Verify patient exists in database
- Try another patient first

### "Intent confidence very low"
- Question may be ambiguous
- Try rephrasing: "Show me the latest blood report"
- Check exact format of expected queries above

### NLP responses are generic
- Claude may need more context
- Try more specific questions
- Ensure diagnostic data is populated in database

### Slow responses
- First request can be slower due to Claude API latency
- Subsequent requests should be faster (< 2 seconds)
- Check internet connection
- Verify API key is valid

## Extending the System

### Adding New Query Types

Edit `backend/app/routers/nlp_query.py`:

1. **Add new data type to intent extraction:**
```python
# In extract_intent()
"primary_data_type": "observation|medication|...|your_new_type"
```

2. **Add query execution logic:**
```python
# In execute_query()
elif data_type == "your_new_type":
    results["data"]["your_new_type"] = [...]
```

3. **Add rendering in frontend:**
```javascript
// In NLPQueryChat.jsx
if (data.your_new_type) {
  return renderYourNewType(data.your_new_type)
}
```

### Customizing Claude Instructions

Modify the prompts in `nlp_query.py`:

- `intent_prompt`: Controls how Claude understands questions
- `summary_prompt`: Controls narrative generation
- Model: Currently using `claude-opus-4-1` (most capable)

### Using Different Claude Models

Change in `nlp_query.py`:
```python
response = client.messages.create(
    model="claude-opus-4-1",  # Change to claude-3-sonnet or claude-3-haiku
    ...
)
```

Models by capability:
- `claude-opus-4-1`: Most intelligent (slower, costs more)
- `claude-3-sonnet`: Balanced (recommended)
- `claude-3-haiku`: Fast, basic responses (costs least)

## Security Considerations

1. **API Key Protection**
   - Never commit `.env` to version control
   - Use environment variables in production
   - Rotate keys periodically

2. **Patient Data**
   - All queries filtered by patient_id
   - No cross-patient data leakage
   - Claude doesn't store conversation data

3. **Rate Limiting** (Recommended)
   - Implement per-user rate limits
   - Prevent abuse of Claude API calls
   - Monitor API usage costs

## Production Deployment

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-xxx
DATABASE_URL=postgresql://user:pass@host/db
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
CORS_ORIGINS=https://yourdomain.com
```

### Database
- Switch from SQLite to PostgreSQL
- Ensure proper backups
- Configure connection pooling

### API Costs
- Each query costs approximately $0.01-0.05 (Claude Opus)
- Budget ~$0.10-0.20 per patient per day if heavily used
- Consider implementing usage quotas

## Support

For issues:
1. Check `.env` configuration
2. Verify Anthropic API key is active
3. Review backend logs: `uvicorn app.main:app --reload`
4. Test API directly: `curl http://localhost:8000/docs`

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure API key
3. ✅ Start backend & frontend
4. ✅ Visit patient detail page
5. ✅ Click "AI Assistant" tab
6. ✅ Ask a question about the patient
