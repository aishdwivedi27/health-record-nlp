# NLP Assistant - Quick Start (5 minutes)

## 1. Get API Key
- Go to https://console.anthropic.com
- Create an API key
- Copy it (starts with `sk-ant-`)

## 2. Configure Backend

```bash
cd backend
```

Create `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## 3. Run Backend

```bash
python -m uvicorn app.main:app --reload
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

## 4. Run Frontend (new terminal)

```bash
cd frontend
npm run dev
```

Visit: `http://localhost:5173`

## 5. Try It

1. Click on any patient
2. Click **"AI Assistant"** tab
3. Ask: `"What are the latest blood reports?"`
4. Done! 🎉

## Sample Questions

```
- Is there a latest blood report available?
- Show me active medications
- Compare last 2 blood reports
- What are the latest vital signs?
- Summarize clinical notes
- Any X-ray reports in the last 3 months?
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ANTHROPIC_API_KEY not found` | Create `.env` file in backend dir with your key |
| `ModuleNotFoundError: anthropic` | Run `pip install -r requirements.txt` |
| Patient not found | Select a different patient or seed the database |
| Slow response | Claude API takes 1-3 seconds, that's normal |

## How It Works

1. **You ask**: "What medications is the patient on?"
2. **Claude understands**: action=list, type=medication, status=active
3. **System queries**: Database fetches active medications
4. **Claude responds**: "The patient is on Metformin 500mg twice daily..."
5. **You see**: 
   - Narrative answer at top
   - Detailed structured data below (click "Show Details")

That's it! The hybrid approach = smart + fast ⚡

## Next: Deploy to Production

See `NLP_SETUP_GUIDE.md` for:
- Production deployment
- Database setup (PostgreSQL)
- Rate limiting
- API cost management
- Security considerations
