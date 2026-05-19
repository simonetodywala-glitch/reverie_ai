import os
import httpx
from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import ScheduleRequest, ScheduleResponse
from backend.auth import verify_token

router = APIRouter()

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _fmt(t: str | None) -> str:
    if not t:
        return "N/A"
    try:
        h, m = map(int, t.split(":"))
        ampm = "AM" if h < 12 else "PM"
        return f"{h % 12 or 12}:{m:02d} {ampm}"
    except Exception:
        return t


@router.post("/calculate", response_model=ScheduleResponse)
async def calculate_schedule(req: ScheduleRequest, _=Depends(verify_token)):
    factors_text = "\n".join(f"- {note}" for note in req.adjustments) if req.adjustments else "- No special factors detected"

    age_line = f"Age: {req.age}" if req.age else "Age: not provided"
    chronotype_map = {"early": "early bird", "night": "night owl", "middle": "neutral"}
    chronotype_line = f"Chronotype: {chronotype_map.get(req.chronotype or '', 'unknown')}"

    extra_context = []
    if req.caffeine_last_cup:
        extra_context.append(f"last caffeine at {_fmt(req.caffeine_last_cup)}")
    if req.last_meal_time:
        extra_context.append(f"last meal at {_fmt(req.last_meal_time)}")
    if req.exercise_timing and req.exercise_timing != "none":
        extra_context.append(f"{req.exercise_timing} exercise today")
    if req.stress_level and req.stress_level >= 4:
        extra_context.append(f"high stress (level {req.stress_level}/5)")
    if req.alcohol_nightly:
        extra_context.append("drinks alcohol most nights")
    if req.shift_work:
        extra_context.append("shift worker / irregular schedule")

    context_line = (", ".join(extra_context)) if extra_context else "no additional lifestyle factors noted"

    prompt = f"""You are a warm, knowledgeable sleep coach writing a personalised bedtime tip for a Reverie app user.

User profile:
- {age_line}
- {chronotype_line}
- Wake time: {_fmt(req.wake_time)}
- Recommended bedtime: {_fmt(req.bedtime)}
- Target sleep: {req.target_hours} hours
- Lifestyle: {context_line}

Factors that adjusted their bedtime tonight:
{factors_text}

Write ONE concise tip (2–3 sentences max) that is:
1. Specific to THEIR bedtime ({_fmt(req.bedtime)}) and the factors above — not generic advice
2. Actionable tonight, not a long-term habit
3. Warm and encouraging, not clinical

Respond with only the tip text, no labels or preamble."""

    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise Exception("GROQ_API_KEY not set")
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
            )
            tip = res.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        tip = f"Tonight, start winding down at {_fmt(req.bedtime)} — dim your lights, put your phone face-down, and give yourself 20 minutes of quiet before sleep."

    return ScheduleResponse(tip=tip)
