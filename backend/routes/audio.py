import os
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
import json
from backend.models.schemas import (
    AudioRequest, AudioResponse, SoundscapeRequest,
    SoundscapeMenuRequest, SoundscapeMenuResponse,
    WinddownRoutineRequest, WinddownRoutineResponse,
    StoryTTSRequest, StoryFromPatternsRequest,
)
from backend.auth import verify_token

router = APIRouter()

GROQ_URL          = "https://api.groq.com/openai/v1/chat/completions"
GROQ_WHISPER_URL  = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL        = "llama-3.3-70b-versatile"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


async def dream_to_story(dream_text: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    prompt = f"""Rewrite this dream as a slow, peaceful, third-person bedtime story (80-100 words).
Soften any anxious or scary elements into something calming and beautiful.
Use gentle, flowing language. End with the character falling peacefully asleep.

Dream: "{dream_text}"
"""
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
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq error {res.status_code}")
        return res.json()["choices"][0]["message"]["content"].strip()


@router.post("/story", response_model=AudioResponse)
async def generate_story(req: AudioRequest, _=Depends(verify_token)):
    try:
        story_text = await dream_to_story(req.dream_text)
        return AudioResponse(audio_url=f"STORY_TEXT:{story_text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/story-from-patterns")
async def story_from_patterns(req: StoryFromPatternsRequest, _=Depends(verify_token)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    summaries_text = "\n".join(f"- {s}" for s in req.dream_summaries[:8] if s.strip())
    emotions_text  = ", ".join(req.emotions[:5]) if req.emotions else "peaceful, calm"
    themes_text    = ", ".join(req.themes[:5])   if req.themes   else "rest, quiet"

    prompt = f"""Based on the recurring themes and emotions from someone's dream journal, write a slow, peaceful, third-person bedtime story (80–100 words).

The story should subtly echo the emotional landscape of their dreams — using similar feelings, imagery, and motifs — but transformed into something calm and beautiful.

Dream journal excerpts:
{summaries_text}

Recurring emotions: {emotions_text}
Recurring themes: {themes_text}

Write a gentle, lullaby-like bedtime story. Use flowing, unhurried language. End with the main character drifting peacefully to sleep. Do not reference dreams or the journal directly."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.75,
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq error {res.status_code}")
        story_text = res.json()["choices"][0]["message"]["content"].strip()
        return {"story_text": story_text}


# ElevenLabs voice IDs for narration — pre-made voices available on all plans
# Rachel: warm calm female  |  Bella: soft intimate female
# Josh: deep storyteller    |  Elli: bright expressive female
_EL_VOICE_MAP = {
    "anxiety":      "21m00Tcm4TlvDq8ikWAM",  # Rachel — warm, grounding
    "fear":         "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "dread":        "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "restlessness": "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "sadness":      "EXAVITQu4vr4xnSDxMaL",  # Bella — gentle, intimate
    "grief":        "EXAVITQu4vr4xnSDxMaL",  # Bella
    "tenderness":   "EXAVITQu4vr4xnSDxMaL",  # Bella
    "nostalgia":    "TxGEqnHWrfWFTfGW9XjX",  # Josh — warm storyteller
    "wonder":       "TxGEqnHWrfWFTfGW9XjX",  # Josh
    "awe":          "TxGEqnHWrfWFTfGW9XjX",  # Josh
    "peaceful":     "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "hope":         "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "joy":          "MF3mGyEYCl7XYWbV9V6O",  # Elli — bright, expressive
    "excitement":   "MF3mGyEYCl7XYWbV9V6O",  # Elli
}
_EL_DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # Rachel


def _pick_el_voice(emotions: list) -> str:
    for e in emotions:
        v = _EL_VOICE_MAP.get(e.lower())
        if v:
            return v
    return _EL_DEFAULT_VOICE


# Groq Orpheus fallback (replaced decommissioned playai-tts)
_ORPHEUS_DEFAULT = "hannah"

def _pick_orpheus_voice(emotions: list) -> str:
    m = {"anxiety":"hannah","fear":"hannah","dread":"diana","restlessness":"hannah",
         "sadness":"diana","grief":"diana","tenderness":"autumn",
         "nostalgia":"austin","wonder":"austin","awe":"austin",
         "peaceful":"autumn","hope":"autumn","joy":"hannah","excitement":"hannah"}
    for e in emotions:
        v = m.get(e.lower())
        if v:
            return v
    return _ORPHEUS_DEFAULT


@router.post("/story-tts")
async def story_tts(req: StoryTTSRequest, _=Depends(verify_token)):
    el_key   = os.getenv("ELEVENLABS_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if el_key:
        voice_id = _pick_el_voice(req.emotions)
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                res = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key":   el_key,
                        "Content-Type": "application/json",
                        "Accept":       "audio/mpeg",
                    },
                    json={
                        "text":     req.story_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability":        0.38,
                            "similarity_boost": 0.80,
                            "style":            0.42,
                            "use_speaker_boost": True,
                        },
                    },
                )
            if res.status_code == 200:
                return StreamingResponse(
                    iter([res.content]),
                    media_type="audio/mpeg",
                    headers={"Content-Disposition": "inline; filename=story.mp3"},
                )
            print(f"ElevenLabs failed ({res.status_code}), falling back to Orpheus")
        except Exception as e:
            print(f"ElevenLabs exception: {e}, falling back to Orpheus")

    if not groq_key:
        raise HTTPException(status_code=501, detail="No TTS API key configured")

    voice = _pick_orpheus_voice(req.emotions)
    # Orpheus free tier: 1200 TPM. Cap at 1500 chars to stay safely under limit.
    groq_text = req.story_text[:1500]
    async with httpx.AsyncClient(timeout=90.0) as client:
        res = await client.post(
            "https://api.groq.com/openai/v1/audio/speech",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model":           "canopylabs/orpheus-v1-english",
                "input":           groq_text,
                "voice":           voice,
                "response_format": "wav",
            },
        )
        if res.status_code == 429:
            raise HTTPException(status_code=429, detail="Audio is cooling down — try again in about 30 seconds.")
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq TTS error {res.status_code}: {res.text}")

    return StreamingResponse(
        iter([res.content]),
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=story.wav"},
    )


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), _=Depends(verify_token)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    audio_data = await file.read()
    filename = file.filename or "dream.webm"
    content_type = file.content_type or "audio/webm"

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            GROQ_WHISPER_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (filename, audio_data, content_type)},
            data={
                "model":    "whisper-large-v3-turbo",
                "language": "en",
                "prompt":   "Personal dream journal entry. The speaker describes a dream they had, including people, places, emotions, and events. May include proper nouns and vivid imagery.",
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Whisper error {res.status_code}: {res.text}")
        return {"text": res.json().get("text", "")}


EMOTION_SOUNDS = {
    "anxiety":     "tense atmospheric hum, low unsettling tones, still and uneasy",
    "fear":        "dark ambient drone, low rumbling, distant hollow echoes",
    "wonder":      "ethereal floating pads, soft crystalline tones, vast and spacious",
    "peaceful":    "gentle rain on leaves, soft wind, distant water, calm and still",
    "joy":         "warm bright ambient tones, light breeze, soft natural textures",
    "sadness":     "melancholic slow pads, quiet and still, soft distant rain",
    "excitement":  "rising ambient energy, open air, subtle pulse and movement",
    "nostalgia":   "warm hazy ambient, soft vintage texture, gentle distant tone",
    "confusion":   "layered shifting tones, overlapping soft textures, slowly drifting",
    "awe":         "vast expansive soundscape, deep reverb, celestial resonance",
    "dread":       "slow building ominous drone, deep bass, cold still air",
    "longing":     "haunting open space, soft resonance, quiet and searching",
    "grief":       "quiet, heavy ambient, very slow movement, deep stillness",
    "hope":        "gentle rising tones, warm pads, soft light texture",
    "tenderness":  "soft warm ambient, intimate and close, gentle and quiet",
    "restlessness":"shifting layered tones, subtle unease, never quite settling",
    "relief":      "slow exhale of sound, warmth returning, open and soft",
    "awe":         "vast reverberant space, deep and slow, celestial and open",
    "pride":       "full warm tones, grounded and steady, quietly expansive",
    "shame":       "withdrawn ambient, quiet and inward, low and soft",
}


def _build_soundscape_prompt(emotions: list, themes: list) -> str:
    descriptors = [EMOTION_SOUNDS[e.lower()] for e in emotions[:3] if e.lower() in EMOTION_SOUNDS]
    if not descriptors:
        descriptors = ["dreamlike ambient atmosphere, soft and immersive"]
    prompt = f"Ambient dreamscape soundscape: {'; '.join(descriptors)}. Atmospheric, immersive, seamlessly loopable, no sudden changes, no melody, pure texture."
    return prompt


async def _freesound_search(query: str, api_key: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(
                "https://freesound.org/apiv2/search/text/",
                params={
                    "query": query,
                    "token": api_key,
                    "fields": "previews,duration",
                    "filter": "duration:[15 TO 180] tag:loop",
                    "page_size": 5,
                    "sort": "score",
                },
            )
            if res.status_code != 200:
                return None
            for r in res.json().get("results", []):
                url = r.get("previews", {}).get("preview-hq-mp3") or r.get("previews", {}).get("preview-lq-mp3")
                if url:
                    return url
    except Exception:
        pass
    return None


@router.post("/soundscape-menu", response_model=SoundscapeMenuResponse)
async def get_soundscape_menu(req: SoundscapeMenuRequest, _=Depends(verify_token)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    SEARCH_QUERY_SCHEMA = '"search_query": "3-6 words for finding a matching loopable ambient recording on Freesound.org"'

    if req.custom_prompt:
        prompt = f"""Generate one ambient sleep soundscape for this description: "{req.custom_prompt}"

Return JSON:
{{
  "soundscapes": [
    {{
      "name": "poetic 2-4 word name",
      "description": "one atmospheric sentence",
      "emoji": "single relevant emoji",
      "base": "one of: rain, ocean, forest, fire, space, storm, cafe",
      {SEARCH_QUERY_SCHEMA},
      "params": {{"filter_freq": <200-8000>, "lfo_rate": <0.03-0.5>, "lfo_depth": <0.05-0.35>, "gain": <0.15-0.75>}}
    }}
  ]
}}"""
    else:
        emotions_str = ", ".join(req.emotions[:5]) if req.emotions else "calm, reflective"
        themes_str   = ", ".join(req.themes[:3])   if req.themes   else "rest"
        prompt = f"""Generate 6 ambient sleep soundscapes for someone whose dream had emotions: {emotions_str}, themes: {themes_str}.

Rules:
- Names are poetic, specific — think ambient album titles
- Descriptions are one atmospheric sentence
- Vary base types across the 6
- search_query should find a real loopable recording (e.g. "gentle rain loop ambient", "ocean waves shore loop")

Return JSON:
{{
  "soundscapes": [
    {{
      "name": "poetic title",
      "description": "one sentence",
      "emoji": "single emoji",
      "base": "rain|ocean|forest|fire|space|storm|cafe",
      {SEARCH_QUERY_SCHEMA},
      "params": {{"filter_freq": <200-8000>, "lfo_rate": <0.03-0.5>, "lfo_depth": <0.05-0.35>, "gain": <0.15-0.75>}}
    }}
  ]
}}"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "response_format": {"type": "json_object"},
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq error {res.status_code}")
        data = json.loads(res.json()["choices"][0]["message"]["content"])

    soundscapes = data.get("soundscapes", [])
    if not soundscapes:
        print("Groq returned no soundscapes:", data)
        raise HTTPException(status_code=500, detail="No soundscapes returned")

    # Fetch real audio from Freesound in parallel (if key available)
    freesound_key = os.getenv("FREESOUND_API_KEY")
    audio_urls = await asyncio.gather(*[
        _freesound_search(s.get("search_query", s.get("base", "ambient loop")), freesound_key)
        for s in soundscapes
    ]) if freesound_key else [None] * len(soundscapes)

    return SoundscapeMenuResponse(soundscapes=[
        {
            "name":         s.get("name", ""),
            "description":  s.get("description", ""),
            "emoji":        s.get("emoji", "🎵"),
            "base":         s.get("base", "rain"),
            "params":       s.get("params", {}),
            "search_query": s.get("search_query"),
            "audio_url":    url,
        }
        for s, url in zip(soundscapes, audio_urls)
    ])


@router.post("/winddown-routine", response_model=WinddownRoutineResponse)
async def get_winddown_routine(req: WinddownRoutineRequest, _=Depends(verify_token)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    emotions_str = ", ".join(req.emotions[:5]) if req.emotions else "calm"
    themes_str   = ", ".join(req.themes[:3])   if req.themes   else "rest"

    prompt = f"""A user is winding down for sleep. Their dream had emotions: {emotions_str}, and themes: {themes_str}.

Choose exactly 3 wind-down activities that fit tonight's emotional content. Pick from this list — vary your choices based on the dream, don't default to the same options every time:

- breathing: slow breath work to calm the nervous system
- body_scan: progressive relaxation from feet to head
- journaling: writing to process what the dream stirred up
- visualization: calming mental imagery to replace difficult feelings
- gratitude: grounding in what felt safe or good today
- story: a gentle AI-narrated bedtime story
- stretching: physical movement to release stored tension

Tone: warm and direct, like a thoughtful friend — not a wellness app.

Return JSON:
{{
  "intention": "one specific sentence for tonight — reference the dream's emotional tone, no clichés",
  "items": [
    {{"type": "<activity from list>", "note": "8-10 words on why this helps tonight specifically"}},
    {{"type": "<activity from list>", "note": "8-10 words"}},
    {{"type": "<activity from list>", "note": "8-10 words"}}
  ]
}}

Order from most to least urgent for tonight. Each type must be unique. Notes must reflect the actual dream emotions."""

    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "response_format": {"type": "json_object"},
            },
        )
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Groq error {res.status_code}")
        data = json.loads(res.json()["choices"][0]["message"]["content"])

    return WinddownRoutineResponse(
        intention=data.get("intention", ""),
        items=[{"type": i.get("type",""), "note": i.get("note","")} for i in data.get("items", [])],
    )


@router.post("/soundscape")
async def generate_soundscape(req: SoundscapeRequest, _=Depends(verify_token)):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")

    prompt = _build_soundscape_prompt(req.emotions, req.themes)

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={"text": prompt, "duration_seconds": 22, "prompt_influence": 0.4},
        )
        if res.status_code != 200:
            print(f"ElevenLabs {res.status_code}: {res.text}")
            try:
                detail = res.json()
            except Exception:
                detail = res.text
            raise HTTPException(status_code=500, detail=f"ElevenLabs error {res.status_code}: {detail}")

        audio_bytes = res.content

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=soundscape.mp3"}
    )
