# ATOM — Autonomous Threat & Operations Monitor

The AI that sits in your war room and thinks faster than your team.

```
    ⚛️ ATOM
    Autonomous Threat & Operations Monitor
    
    Real-time incident intelligence agent
    for Google Gemini Live Agent Hackathon
```

---

## 🎯 What is ATOM?

ATOM is like **Jarvis from Iron Man but for production incidents**. It's not a monitoring tool — it's an **active participant in the crisis**.

It simultaneously:
- **Listens** to the live voice call happening in your war room
- **Watches** the team's screens (screenshots updated every 5 seconds)
- **Reads** real-time production logs streaming from your systems
- **Interrupts** engineers when it spots the root cause
- **Proactively alerts** when SLA breach is imminent (under 3 minutes)
- **Never panics** — it's the calmest person in the room

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ATOM Backend                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Google Gemini Live API Session              │   │
│  │  (Audio, Vision, Text - 1 persistent connection)    │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   ↑ ↓                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │          3 Concurrent Data Pipelines               │    │
│  │  ┌─────────────┐ ┌───────────┐ ┌──────────────┐   │    │
│  │  │ Audio       │ │ Vision    │ │ Logs         │   │    │
│  │  │ Microphone  │ │ Screenshots│ │ Production   │   │    │
│  │  │ PyAudio     │ │ PIL        │ │ Pub/Sub      │   │    │
│  │  └─────────────┘ └───────────┘ └──────────────┘   │    │
│  └────────────────────────────────────────────────────┘    │
│                       ↓                                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │         State Management (Firestore)               │    │
│  │   Timeline | Hypotheses | Postmortem               │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
         ↓ WebSocket
┌─────────────────────────────────────────────────────────────┐
│              React + Vite Frontend (War Room UI)             │
│  ┌──────────────────────┬──────────────────────────────┐   │
│  │ ATOM Feed            │ SLA Countdown               │   │
│  │ & Timeline           │ & Postmortem                │   │
│  │                      │                              │   │
│  │ Real-time updates    │ Dramatic visualizations     │   │
│  │ Event streaming      │ Live document generation    │   │
│  └──────────────────────┴──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key
- GCP account (optional, for deployment)

### 1. Clone & Setup

```bash
git clone <repo>
cd atom

# Create .env file
cp .env .env.local
# Edit .env.local with your API keys
```

### 2. Backend Setup

```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Run backend 
uvicorn backend.main:app --reload --port 8000
```

Backend will start at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Start dev server
npm run dev
```

Frontend will start at `http://localhost:5173`

### 4. Launch Demo

1. Open http://localhost:5173 in browser
2. Click **"Start Incident"** button
3. Watch ATOM respond in real-time as incident logs stream in
4. Observe the dramatic SLA countdown
5. See postmortem auto-generate as incident resolves

## 📡 API Endpoints

### Start Incident
```
POST /incident/start
Content-Type: application/json

{
  "name": "Production Incident",
  "incident_type": "simulated"
}
```

### Stop Incident
```
POST /incident/{id}/stop
```

### Get Incident Status
```
GET /incident/{id}
```

### WebSocket Real-Time Updates
```
WS /ws
```

## 🧠 How ATOM Works

### 1. **Multi-modal Input**
- **Audio**: Captures microphone stream (16kHz, 16-bit PCM)
- **Vision**: Screenshots every 5 seconds, compressed to 1280x720
- **Logs**: Production events from Pub/Sub or simulator

### 2. **Gemini Live API**
- Single persistent WebSocket connection
- Receives all modalities simultaneously
- Uses Charon voice (deep, authoritative)
- System prompt shapes behavior to never wait, always interrupt

### 3. **Context Awareness**
- Maintains timeline of all events in Firestore
- Builds hypotheses as new evidence appears
- Triggers urgent alerts for SLA breaches
- Can cite specific logs ("Logs at 14:32 show...")

### 4. **Proactive Interruption**
- Detects barge-in (when team speaks over ATOM)
- Watches SLA countdown for breaches < 3 minutes
- Suggests root cause with evidence
- Drives team toward resolution

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI** | Google Gemini 2.0 Flash Live API |
| **Backend** | Python 3.11, FastAPI, asyncio |
| **Streaming** | WebSockets, PyAudio, Pillow |
| **State** | Google Firestore |
| **Logs** | GCP Pub/Sub (simulated) |
| **Frontend** | React 18, Vite, Tailwind CSS |
| **UI/UX** | Dark theme, high contrast, cinematic |
| **Deployment** | Google Cloud Run, Terraform |

## ⚙️ Customization

### Adjust Log Sequence

Edit [backend/pipelines/logs.py](backend/pipelines/logs.py) in the `DEMO_LOGS` array to customize the incident scenario.

### Change SLA Trigger Time

Modify the SLA message in the logs to change when breach warnings appear.

### Customize ATOM's System Prompt

Edit `ATOMSession.SYSTEM_PROMPT` in [backend/gemini/session.py](backend/gemini/session.py)

### UI Theme

Modify colors in [frontend/tailwind.config.js](frontend/tailwind.config.js)

## 🚢 Deployment

### To Google Cloud Run

```bash
# 1. Set up GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/atom

# 3. Deploy with Terraform
cd infra
terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID"
terraform apply -var="project_id=YOUR_PROJECT_ID"

# 4. Build and deploy frontend
cd ../frontend
npm run build
gcloud app deploy
```

## 🎭 Demo Scenario

When you click "Start Incident", this sequence plays out:

| Time | Event | ATOM Response |
|------|-------|---------------|
| 0:00 | Deployment initiated | - |
| 0:15 | Deployment succeeds | - |
| 0:30 | Error rate rises to 2.3% | - |
| 0:45 | Error rate spikes to 18.7% | "I'm detecting correlation..." |
| 1:00 | DB connection pool exhausted | "Root cause appears to be..." |
| 1:15 | Payments service latency 4200ms | **"SLA BREACH IMMINENT"** |
| 1:30 | 180 seconds to breach | Countdown starts |
| 1:45 | 90 seconds to breach | **Flashing red** |
| 2:00 | Rollback initiated | "Executing rollback now..." |
| 2:15 | Error rates normalizing | "Recovery in progress..." |
| 2:30 | Systems nominal | **"INCIDENT RESOLVED"** |

## 📊 Firestore Document Structure

```
incidents/{incident_id}/
├── id: "abc123"
├── status: "active" | "resolved"
├── created_at: Timestamp
├── sla_deadline: Timestamp
├── timeline: [...]
├── hypotheses: [...]
├── postmortem: {...}
└── resolved_at: Timestamp
```

## 🎨 UI Components

### SLA Countdown
- Large dramatic clock with color transitions
- Green → Amber (5 min) → Red (2 min) → Flashing Red (30 sec)
- Shows "SLA BREACH IMMINENT" banner at 2 minutes

### ATOM Feed
- Real-time message stream from ATOM
- Green highlights for ATOM insights
- Auto-scrolls to latest messages
- "ATOM is listening..." when quiet

### Timeline
- Color-coded by severity (INFO, WARNING, ERROR, CRITICAL)
- Shows timestamp and source for each event
- Auto-scrolls to latest event

### Postmortem
- Live document generation during incident
- Sections: Summary, Root Cause, Impact, Resolution, Action Items
- Export to Markdown when resolved

## 📝 Project Structure

```
atom/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile
│   ├── gemini/
│   │   ├── __init__.py
│   │   └── session.py          # Gemini Live API
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── audio.py            # Microphone streaming
│   │   ├── vision.py           # Screenshot capture
│   │   └── logs.py             # Log simulation
│   └── state/
│       ├── __init__.py
│       └── firestore.py        # State management
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── SLACountdown.jsx
│           ├── WhispererFeed.jsx
│           ├── Timeline.jsx
│           └── Postmortem.jsx
├── infra/
│   └── main.tf                 # Terraform for GCP
├── .env                        # Environment variables
└── README.md
```

## 🔧 Troubleshooting

### Backend won't start
```bash
python --version  # Must be 3.11+
pip list | grep fastapi
```

### Frontend WebSocket connection fails
```bash
curl http://localhost:8000/health
```

### "GEMINI_API_KEY not set"
```bash
echo "GEMINI_API_KEY=your_key_here" >> .env
echo "GCP_PROJECT_ID=your_project_id" >> .env
```

## 🎓 Learn More

- [Google Gemini Live API Docs](https://ai.google.dev/live)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)

## 📄 License

Built for Google Gemini Live Agent Hackathon 2024

---

**ATOM: The only one in the room who never panics. ⚛️**
