// ─────────────────────────────────────────
// REVERIE — api.js
// All fetch calls to the FastAPI backend
// ─────────────────────────────────────────

const BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : 'https://reverie-aiproject.onrender.com';

// Set by auth.js after login so every request carries a fresh Firebase ID token
let _firebaseUser = null;
window._setReverieUser = (user) => { _firebaseUser = user; };

async function _authHeaders() {
  if (!_firebaseUser) return {};
  const token = await _firebaseUser.getIdToken();
  return { 'Authorization': `Bearer ${token}` };
}

// ── DREAMS ──

async function analyzeDream(dreamText, { wakingContext, eyeDominance, handedness } = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}/dreams/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
      body: JSON.stringify({
        text:            dreamText,
        waking_context:  wakingContext || null,
        eye_dominance:   eyeDominance  || null,
        handedness:      handedness    || null,
      })
    });
  } catch {
    throw new Error('Cannot reach the Reverie backend. Make sure it is running: uvicorn backend.main:app --reload');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Backend error ${res.status}`);
  }
  return res.json();
}

// ── INSIGHTS ──

async function sendChatMessage(userId, message, dreamContext = null, history = []) {
  const res = await fetch(`${BASE_URL}/analysis/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ user_id: userId, message, dream_context: dreamContext, history })
  });
  if (!res.ok) throw new Error('Chat failed');
  return res.json();
}

async function getPatternReport(dreams) {
  const res = await fetch(`${BASE_URL}/analysis/patterns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ dreams })
  });
  if (!res.ok) throw new Error('Failed to get pattern report');
  return res.json();
}

// ── SLEEP SCHEDULE ──

async function getSleepTip(profile, result) {
  const res = await fetch(`${BASE_URL}/schedule/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({
      wake_time:         profile.wakeTime,
      bedtime:           result.bedtime,
      target_hours:      result.targetSleepHours,
      age:               profile.age              || null,
      caffeine_last_cup: profile.caffeineLastCup  || null,
      last_meal_time:    profile.lastMealTime      || null,
      exercise_timing:   profile.exerciseTiming    || 'none',
      stress_level:      profile.stressLevel       || 2,
      alcohol_nightly:   profile.alcoholNightly    || false,
      shift_work:        profile.shiftWork         || false,
      chronotype:        profile.chronotype        || null,
      adjustments:       (result.adjustments || []).map(a => a.note),
    })
  });
  if (!res.ok) throw new Error('Tip generation failed');
  return res.json();
}

// ── AUDIO ──

async function transcribeAudio(audioBlob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'dream.webm');
  let res;
  try {
    res = await fetch(`${BASE_URL}/audio/transcribe`, {
      method: 'POST',
      headers: { ...await _authHeaders() },
      body: formData
    });
  } catch {
    throw new Error('Cannot reach the Reverie backend.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Transcription error ${res.status}`);
  }
  return res.json();
}

async function rescriptDream(dreamText, emotions = [], themes = []) {
  const res = await fetch(`${BASE_URL}/dreams/rescript`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ dream_text: dreamText, emotions, themes })
  });
  if (!res.ok) throw new Error('Rescript failed');
  return res.json();
}

async function generateStoryFromPatterns(dreamSummaries, emotions = [], themes = []) {
  const res = await fetch(`${BASE_URL}/audio/story-from-patterns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ dream_summaries: dreamSummaries, emotions, themes })
  });
  if (!res.ok) throw new Error('Pattern story generation failed');
  return res.json();
}

async function generateBedtimeStory(dreamText) {
  const res = await fetch(`${BASE_URL}/audio/story`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ dream_text: dreamText })
  });
  if (!res.ok) throw new Error('Story generation failed');
  return res.json();
}

async function readStoryTTS(storyText, emotions = [], themes = []) {
  const res = await fetch(`${BASE_URL}/audio/story-tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ story_text: storyText, emotions, themes })
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `TTS error ${res.status}`);
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

async function getWinddownRoutine(emotions = [], themes = []) {
  const res = await fetch(`${BASE_URL}/audio/winddown-routine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ emotions, themes })
  });
  if (!res.ok) throw new Error('Routine generation failed');
  return res.json();
}

async function getSoundscapeMenu(emotions = [], themes = [], customPrompt = null) {
  const res = await fetch(`${BASE_URL}/audio/soundscape-menu`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ emotions, themes, custom_prompt: customPrompt })
  });
  if (!res.ok) throw new Error('Soundscape menu failed');
  return res.json();
}

async function getSoundscape(emotions, themes = []) {
  const res = await fetch(`${BASE_URL}/audio/soundscape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...await _authHeaders() },
    body: JSON.stringify({ emotions, themes })
  });
  if (!res.ok) throw new Error('Soundscape generation failed');
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
