# Running the EHR PoC on Windows — No Docker Required

## Prerequisites

1. **Python 3.11+** — https://www.python.org/downloads/windows/
   - During install: tick "Add Python to PATH"
2. **Node.js 20+** — https://nodejs.org/en/download
3. **VS Code** — https://code.visualstudio.com/

---

## Setup (one time)

Open the `ehr-poc` folder in VS Code, then open two terminals: **Terminal → New Terminal**.

### Terminal 1 — Backend

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed the database
python -m app.seed.seed_data

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

API docs available at: http://localhost:8000/docs

---

### Terminal 2 — Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

You should see:
```
  VITE v5.x  ready in Xms
  ➜  Local:   http://localhost:5173/
```

Open http://localhost:5173 in your browser.

---

## Daily startup (after first setup)

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

---

## Re-seed the database

If you want to reset all data back to the original 3 patients:

```bash
cd backend
venv\Scripts\activate
python -m app.seed.seed_data
```

This deletes and re-creates all records.

---

## Troubleshooting

**"venv\Scripts\activate is not recognised"**
Run this first in VS Code terminal:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating again.

**"Port 8000 already in use"**
Find and kill the process:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

**"Module not found" errors**
Make sure the virtual environment is activated — you should see `(venv)` at the start of your terminal prompt.

**CORS errors in browser**
The backend already allows all origins. Make sure the backend is running on port 8000 before starting the frontend.
