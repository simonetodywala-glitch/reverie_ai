# ─────────────────────────────────────────
# REVERIE — routes/dreams.py
# Dream CRUD + Groq AI emotion/theme analysis
# ─────────────────────────────────────────

import os
import json
import httpx
from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import DreamRequest, DreamAnalysis, DreamRescriptRequest
from backend.auth import verify_token

router = APIRouter()

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_DREAM_CHARS = 4000


async def _call_groq(prompt: str, json_mode: bool = True) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in backend/.env")
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        if res.status_code != 200:
            detail = res.json().get("error", {}).get("message", f"Groq error {res.status_code}")
            raise HTTPException(status_code=500, detail=detail)
        return res.json()["choices"][0]["message"]["content"]


def _build_user_context(req: DreamRequest) -> tuple[str, str]:
    """Returns (profile_block, waking_block) to inject into the prompt."""
    profile_parts = []

    if req.eye_dominance and req.eye_dominance != "unsure":
        if req.eye_dominance == "left":
            style = "left-eye dominant — tends toward right-hemisphere processing (holistic, spatial, metaphorical, emotionally intuitive)"
        else:
            style = "right-eye dominant — tends toward left-hemisphere processing (analytical, sequential, detail-oriented, logical)"

        cross = (
            req.handedness in ("right", "left") and
            req.eye_dominance in ("left", "right") and
            req.eye_dominance != req.handedness[0]  # e.g. right-handed + left-eye
        )
        if cross:
            style += ". CROSS-DOMINANT: opposite hand/eye dominance — research links this to more flexible hemispheric communication and often more vivid or unconventional dream imagery"

        profile_parts.append(f"Cognitive style: {style}")

    if req.handedness:
        profile_parts.append(f"Handedness: {req.handedness}")

    profile_block = "\n".join(profile_parts)
    waking_block  = req.waking_context.strip() if req.waking_context else ""
    return profile_block, waking_block


@router.post("/analyze", response_model=DreamAnalysis)
async def analyze_dream(req: DreamRequest, _=Depends(verify_token)):
    dream_text = req.text[:MAX_DREAM_CHARS]
    profile_block, waking_block = _build_user_context(req)

    context_section = ""
    if profile_block:
        context_section += f"\nUser cognitive profile:\n{profile_block}\n"
    if waking_block:
        context_section += f"\nWhat's on the user's mind today (waking life context):\n\"{waking_block}\"\n"

    waking_instructions = ""
    if waking_block:
        waking_instructions = """
  "waking_connections": "1-2 specific sentences directly connecting imagery or emotions in THIS dream to the waking life context the user shared. Be concrete — name the dream element and the life situation. Do not be generic.","""

    mind_instructions = ""
    if profile_block:
        mind_instructions = """
  "mind_note": "1 sentence about how the user's cognitive processing style (eye dominance / cross-dominance) may relate to the character or emotional texture of this specific dream.","""

    prompt = f"""You are Reverie — a calm, curious dream companion. Your job is to help someone understand their dream in a way that feels personal and real, not like a textbook.
{context_section}
Dream:
\"\"\"
{dream_text}
\"\"\"

Read this like a friend who's genuinely interested — notice the specific details, the feelings underneath the surface, what might be quietly connected to their waking life. Be warm, a little poetic, grounded. No jargon. No generic interpretations. Speak directly to the dreamer using "you".

Respond ONLY with a valid JSON object — no markdown, no extra text.

{{
  "emotions": ["word1", "word2"],
  "themes": ["specific dream element · what it might mean for them", "specific dream element · what it might mean for them"],
  "summary": "2-3 sentences that capture the feeling and meaning of this dream. Speak directly to them — casual, warm, like you're telling them something interesting you noticed. Use 'you'.",
  "interpretation": "1-2 paragraphs going a little deeper. Reference specific images from the dream. What might their mind be quietly working through? Stay grounded, not mystical.",
  "reflections": [
    "A calm, curious question about one specific detail or moment in the dream?",
    "A question that connects something in the dream to how they might be feeling lately?",
    "A gentle question that invites them to sit with something unresolved?"
  ],
  "is_nightmare": false{waking_instructions}{mind_instructions}
}}

Emotion words: wonder, anxiety, joy, fear, sadness, excitement, nostalgia, peaceful, confusion, hope, longing, dread, awe, grief, frustration, tenderness, shame, pride, restlessness, relief.
Use 2-5 emotions. Themes must reference actual elements from this specific dream — nothing generic.

For "is_nightmare": true ONLY if the dream was genuinely frightening or distressing in a way that would disrupt sleep — e.g. being chased, attacked, witnessing violence, helplessness, death of a loved one. Weird, funny, or anxious-but-harmless dreams are NOT nightmares even if they contain anxiety or fear emotions."""

    try:
        raw  = await _call_groq(prompt)
        data = json.loads(raw)
        return DreamAnalysis(**data)
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/rescript")
async def rescript_dream(req: DreamRescriptRequest, _=Depends(verify_token)):
    emotion_context = ", ".join(req.emotions) if req.emotions else "distressing"
    prompt = f"""You are helping someone practice Imagery Rehearsal Therapy (IRT) for nightmare relief.

They had this dream:
"{req.dream_text[:3000]}"

Emotions felt: {emotion_context}

Rewrite this dream keeping the same setting, characters, and opening — but change the middle or ending so it resolves in an empowering, peaceful, or meaningful way. The rescripted version should:
- Keep the dream's imagery and atmosphere (don't make it completely different)
- Transform threatening or distressing elements into something resolved, safe, or empowering
- End with a sense of calm, safety, or strength
- Be written in first-person dream style
- Be roughly the same length as the original (150–250 words)

Write only the rescripted dream. No explanation, no preamble."""

    text = await _call_groq(prompt, json_mode=False)
    return {"rescripted_text": text}


@router.post("/summarize")
async def summarize_dream(req: dict, _=Depends(verify_token)):
    text = req.get("dream_text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="dream_text required")
    prompt = f"""Condense this dream analysis into 2-3 plain sentences. What's the core emotional takeaway? What does it mean for this person? Write warmly and directly, like a friend giving the one-line version. No bullet points, no headers.

Analysis:
{text[:3000]}

Write only the condensed summary."""
    summary = await _call_groq(prompt, json_mode=False)
    return {"summary": summary}


async def _call_groq_chat(messages: list, json_mode: bool = False) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.8,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        if res.status_code != 200:
            detail = res.json().get("error", {}).get("message", f"Groq error {res.status_code}")
            raise HTTPException(status_code=500, detail=detail)
        return res.json()["choices"][0]["message"]["content"]


@router.post("/chat-message")
async def dream_chat_message(req: dict, _=Depends(verify_token)):
    message        = req.get("message", "").strip()
    history        = req.get("history", [])
    exchange_count = sum(1 for h in history if h.get("role") == "user")
    can_wrap       = exchange_count >= 4

    system = f"""You are Reverie — a warm, genuinely curious dream companion having a natural conversation to understand someone's dream.

Your personality:
- Sound like a caring friend who knows a lot about the mind — not a therapist, not a chatbot
- Use plain everyday language. If you use any psychology term explain it immediately in simple words
- Be warm, genuinely curious, occasionally a little playful
- Keep responses SHORT — 2-3 sentences max, then one question
- Ask ONLY ONE question at a time, never two
- Reference specific details from what they said to show you're listening

Your goal: understand the full dream story, uncover emotions felt during and after, spot key symbols and people, find waking life connections if they come up naturally.

{"You have had enough exchanges. You may set ready: true if you genuinely have a solid picture of this dream." if can_wrap else "Set ready: false — keep the conversation going."}

NOTES — this is critical. After EVERY user message (including the very first), you MUST write at least 1-3 notes. Never return an empty notes array. Notes are a clinician's shorthand — 3-7 words each, written like a sharp therapist quietly jotting something down. Start with what you can observe immediately: the setting, the emotional tone, the key image or person mentioned. As the conversation deepens, add more specific observations and replace obvious ones with sharper ones. Cumulative — keep all notes from prior turns, update and add.

Good note examples: "recurring invisibility / feeling unheard", "school = performance anxiety pattern", "waking life stress likely connected", "possible lucid awareness", "authority figure avoidance theme", "fragmented setting — possible sleep disruption", "emotional disconnection from others", "chased — unresolved avoidance pattern", "unfamiliar house — identity in transition", "lost / searching — lack of direction waking life".

Early notes can be simpler: "dream set in childhood home", "running / urgency theme", "felt confused throughout", "friend appears as stranger". These are fine for the first 1-2 turns. Deepen them as you learn more. Never leave notes empty.

ALWAYS respond with valid JSON only, no text before or after:
{{
  "reply": "your warm conversational response with one question at the end",
  "notes": ["at least 1 note here — never empty"],
  "ready": false
}}"""

    msgs = [{"role": "system", "content": system}]
    for h in history:
        msgs.append({"role": h["role"], "content": h["content"]})
    if message:
        msgs.append({"role": "user", "content": message})

    try:
        raw  = await _call_groq_chat(msgs, json_mode=True)
        data = json.loads(raw)
        return {
            "reply": data.get("reply", "Tell me about your dream — whatever you remember."),
            "notes": data.get("notes", []),
            "ready": bool(data.get("ready", False)) and can_wrap,
        }
    except Exception:
        return {
            "reply": "I'm here — tell me about your dream, whatever you remember.",
            "notes": [],
            "ready": False,
        }


@router.post("/chat-finalize")
async def dream_chat_finalize(req: dict, _=Depends(verify_token)):
    history = req.get("history", [])
    conversation = "\n".join([
        f"{'User' if h['role'] == 'user' else 'Reverie'}: {h['content']}"
        for h in history if h.get("role") in ("user", "assistant")
    ])

    prompt = f"""Based on this conversation about someone's dream, write a deep and thoughtful analysis. You know this dream well.

Conversation:
{conversation[:5000]}

Write in a warm, conversational tone — like an educated friend explaining something meaningful. No clinical language. If you use any psychology term explain it right away in plain words. Use "you" to speak directly to the person.

Return ONLY valid JSON:
{{
  "dream_text": "reconstruct the dream narrative in 2-3 sentences from what was shared",
  "emotions": ["every distinct emotion present — be specific, there may be 2 or there may be 8, only include ones genuinely present"],
  "themes": ["conceptual themes formatted as element · what it means for this person — like the lion · a symbol of something overwhelming you're trying to outrun"],
  "summary": "2-3 sentences. Warm, direct, use 'you'. Capture both the feeling and the meaning.",
  "interpretation": "2-3 paragraphs. Reference specific images from the dream. What might their mind be quietly working through? Warm and grounded, no jargon.",
  "reflections": ["one specific genuinely useful question about the dream", "one gentle question connecting the dream to their waking life"],
  "personal_connections": "1-2 sentences connecting dream elements to their waking life from the conversation. Write null if nothing came up.",
  "is_nightmare": false
}}"""

    try:
        raw  = await _call_groq(prompt, json_mode=True)
        data = json.loads(raw)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis generation failed: {str(e)}")


@router.post("/general-chat")
async def general_chat(req: dict, _=Depends(verify_token)):
    message = req.get("message", "").strip()
    history = req.get("history", [])

    system = """You are Reverie — a warm, curious mind companion. You're here to talk about whatever is on someone's mind.

You know a lot about dreams, sleep, and the subconscious, but you're equally happy discussing life, emotions, stress, relationships, or just what's been going on lately.

Your personality:
- Sound like a caring friend who knows a lot about the mind — not a therapist, not a chatbot
- Use plain everyday language. No jargon
- Be warm, genuinely curious, occasionally a little playful
- Keep responses SHORT — 2-3 sentences max, then one question if it feels natural
- Reference specific things they said to show you're really listening
- If they describe a dream, explore it naturally and warmly — but don't force analysis
- Never give a list of bullet points. Just talk."""

    msgs = [{"role": "system", "content": system}]
    for h in history:
        msgs.append({"role": h["role"], "content": h["content"]})
    if message:
        msgs.append({"role": "user", "content": message})

    try:
        reply = await _call_groq_chat(msgs, json_mode=False)
        return {"reply": reply.strip()}
    except Exception:
        return {"reply": "I'm here — what's on your mind?"}


@router.get("/{user_id}")
async def get_dreams(user_id: str):
    return {"dreams": [], "count": 0}
