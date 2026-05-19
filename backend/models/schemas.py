# ─────────────────────────────────────────
# REVERIE — schemas.py
# Pydantic models for request/response validation
# ─────────────────────────────────────────

from pydantic import BaseModel
from typing import List, Optional


class DreamRequest(BaseModel):
    text: str
    user_id: Optional[str] = "demo-user"
    waking_context: Optional[str] = None   # what's on the user's mind today
    eye_dominance: Optional[str] = None    # "left", "right", or "unsure"
    handedness: Optional[str] = None       # "right", "left", or "ambidextrous"


class DreamAnalysis(BaseModel):
    emotions: List[str]
    themes: List[str]
    summary: str
    interpretation: str
    reflections: List[str]
    waking_connections: Optional[str] = None
    mind_note: Optional[str] = None
    is_nightmare: Optional[bool] = None  # true only if genuinely distressing/frightening


class ChatMessage(BaseModel):
    role: str     # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    dream_context: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str


class ScheduleRequest(BaseModel):
    wake_time: str                          # "07:00"
    bedtime: str                            # already-calculated bedtime from sleepEngine
    target_hours: float                     # e.g. 8.5
    age: Optional[int] = None
    caffeine_last_cup: Optional[str] = None  # "HH:MM" or null
    last_meal_time: Optional[str] = None
    exercise_timing: Optional[str] = "none"
    stress_level: Optional[int] = 2
    alcohol_nightly: Optional[bool] = False
    shift_work: Optional[bool] = False
    chronotype: Optional[str] = None
    adjustments: Optional[List[str]] = []   # human-readable factor notes


class ScheduleResponse(BaseModel):
    tip: str                                # Gemini-generated personalized advice


class AudioRequest(BaseModel):
    dream_text: str


class AudioResponse(BaseModel):
    audio_url: str


class StoryTTSRequest(BaseModel):
    story_text: str
    emotions: List[str] = []
    themes: List[str] = []


class StoryFromPatternsRequest(BaseModel):
    dream_summaries: List[str]
    emotions: List[str] = []
    themes: List[str] = []


class DreamRescriptRequest(BaseModel):
    dream_text: str
    emotions: List[str] = []
    themes: List[str] = []


class SoundscapeRequest(BaseModel):
    emotions: List[str]
    themes: List[str] = []


class PatternDream(BaseModel):
    date: Optional[str] = None
    emotions: List[str]
    themes: List[str]
    summary: str


class PatternRequest(BaseModel):
    dreams: List[PatternDream]


class PatternReport(BaseModel):
    top_emotions: List[str]
    recurring_themes: List[str]
    narrative: str
    insight: str
    reflections: List[str]


class WinddownRoutineRequest(BaseModel):
    emotions: List[str] = []
    themes: List[str] = []


class WinddownRoutineItem(BaseModel):
    type: str   # breathing | journaling | story
    note: str   # short personalized reason


class WinddownRoutineResponse(BaseModel):
    intention: str
    items: List[WinddownRoutineItem]


class SoundscapeMenuRequest(BaseModel):
    emotions: List[str] = []
    themes: List[str] = []
    custom_prompt: Optional[str] = None


class SoundscapeItem(BaseModel):
    name: str
    description: str
    emoji: str
    base: str
    params: dict = {}
    audio_url: Optional[str] = None
    search_query: Optional[str] = None


class SoundscapeMenuResponse(BaseModel):
    soundscapes: List[SoundscapeItem]
