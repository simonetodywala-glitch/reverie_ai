# ─────────────────────────────────────────
# REVERIE — main.py
# FastAPI app entry point
# Run with: uvicorn backend.main:app --reload
# ─────────────────────────────────────────

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import dreams, analysis, schedule, audio

app = FastAPI(title="Reverie API", version="0.1.0")

# Allow the frontend (running on Live Server) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(dreams.router,   prefix="/dreams",   tags=["Dreams"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(audio.router,    prefix="/audio",    tags=["Audio"])


@app.get("/")
def root():
    return {"message": "Reverie API is running 🌙"}
