# 🌙 Reverie
**Dream smarter. Sleep better.**

AI-powered sleep and dream companion web app.
Built for the AI Startup Challenge Capstone Project.

**Team:** Simone (AI & Backend) · Diego (Frontend) · Megan (Business & Content)

---

## Tech Stack
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Backend:** Python + FastAPI
- **Database:** Firebase Firestore
- **AI:** Google Gemini API
- **Audio:** ElevenLabs API
- **Auth:** Firebase Authentication

## Project Structure
```
reverie/
├── frontend/
│   ├── index.html          # Home screen
│   ├── pages/
│   │   ├── dreams.html     # Dream library
│   │   ├── journal.html    # Log a dream
│   │   ├── insights.html   # AI pattern analysis + chatbot
│   │   ├── winddown.html   # Wind-down routines
│   │   └── profile.html    # User profile + sleep schedule
│   ├── css/
│   │   ├── styles.css      # Global styles + theme variables
│   │   └── components.css  # Reusable UI components
│   └── js/
│       ├── app.js          # App init, theme switching, nav
│       ├── api.js          # All calls to FastAPI backend
│       ├── auth.js         # Firebase auth (login/signup)
│       └── firebase.js     # Firebase config + Firestore helpers
├── backend/
│   ├── main.py             # FastAPI app entry point
│   ├── routes/
│   │   ├── dreams.py       # Dream CRUD endpoints
│   │   ├── analysis.py     # Gemini AI endpoints
│   │   ├── schedule.py     # Sleep schedule logic
│   │   └── audio.py        # ElevenLabs endpoints
│   ├── models/
│   │   └── schemas.py      # Pydantic data models
│   └── requirements.txt    # Python dependencies
└── docs/
    ├── week1.pdf
    └── week2.pdf
```

## How to Run (see full steps in RUNNING.md)
1. Install Python dependencies: `pip install -r backend/requirements.txt`
2. Start backend: `uvicorn backend.main:app --reload`
3. Open `frontend/index.html` with Live Server in VS Code
