// ─────────────────────────────────────────
// REVERIE — firebase.js
// Firebase config + Firestore database helpers
// ─────────────────────────────────────────

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getFirestore,
  doc,
  setDoc,
  getDoc,
  addDoc,
  getDocs,
  collection,
  query,
  orderBy,
  limit,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

// ── CONFIG ──
const firebaseConfig = {
  apiKey: "AIzaSyDfz7_RNNfjqIvkwA7faYDFMedBisaYDAY",
  authDomain: "reverie-ai-caa66.firebaseapp.com",
  projectId: "reverie-ai-caa66",
  storageBucket: "reverie-ai-caa66.firebasestorage.app",
  messagingSenderId: "311270900598",
  appId: "1:311270900598:web:8390c79ac8ea411b78b057",
  measurementId: "G-BNJ6ZQ5EB9"
};

// ── INIT ──
export const app = initializeApp(firebaseConfig);
export const db  = getFirestore(app);

// ─────────────────────────────────────────
// USER PROFILE
// ─────────────────────────────────────────

export async function saveUserProfile(uid, data) {
  await setDoc(doc(db, "users", uid), data, { merge: true });
}

export async function getUserProfile(uid) {
  const snap = await getDoc(doc(db, "users", uid));
  return snap.exists() ? snap.data() : null;
}

// ─────────────────────────────────────────
// DREAMS
// ─────────────────────────────────────────

// dreamData: { text, emotions, themes, summary }
export async function saveDream(uid, dreamData) {
  const ref = collection(db, "users", uid, "dreams");
  const docRef = await addDoc(ref, {
    ...dreamData,
    createdAt: serverTimestamp()
  });
  return docRef.id;
}

export async function getDreams(uid) {
  const ref  = collection(db, "users", uid, "dreams");
  const q    = query(ref, orderBy("createdAt", "desc"));
  const snap = await getDocs(q);
  return snap.docs.map(d => ({ id: d.id, ...d.data() }));
}

export async function getDream(uid, dreamId) {
  const snap = await getDoc(doc(db, "users", uid, "dreams", dreamId));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

export async function updateDream(uid, dreamId, data) {
  await setDoc(doc(db, "users", uid, "dreams", dreamId), data, { merge: true });
}

export async function saveRescriptedDream(uid, dreamId, rescriptedText) {
  await setDoc(doc(db, "users", uid, "dreams", dreamId),
    { rescriptedText, rescriptedAt: serverTimestamp() }, { merge: true });
}

export async function saveChatHistory(uid, dreamId, history) {
  await setDoc(doc(db, "users", uid, "dreams", dreamId), { chatHistory: history }, { merge: true });
}

export async function getChatHistory(uid, dreamId) {
  const snap = await getDoc(doc(db, "users", uid, "dreams", dreamId));
  return snap.exists() ? (snap.data().chatHistory || []) : [];
}

// ─────────────────────────────────────────
// SLEEP SCHEDULES
// ─────────────────────────────────────────

// scheduleData: { bedtime, bedtimeRange, targetSleepHours, adjustments, wakeTime }
export async function saveSleepSchedule(uid, scheduleData) {
  const ref = collection(db, "users", uid, "sleepSchedules");
  const docRef = await addDoc(ref, {
    ...scheduleData,
    createdAt: serverTimestamp()
  });
  return docRef.id;
}

export async function getLatestSleepSchedule(uid) {
  const ref  = collection(db, "users", uid, "sleepSchedules");
  const q    = query(ref, orderBy("createdAt", "desc"), limit(1));
  const snap = await getDocs(q);
  if (snap.empty) return null;
  const d = snap.docs[0];
  return { id: d.id, ...d.data() };
}

// ─────────────────────────────────────────
// SLEEP LOGS
// ─────────────────────────────────────────

// logData: { bedtime, wakeTime, hoursSlept, date }
export async function saveSleepLog(uid, logData) {
  const ref = collection(db, "users", uid, "sleepLogs");
  await addDoc(ref, { ...logData, createdAt: serverTimestamp() });
}

export async function getRecentSleepLogs(uid) {
  const ref  = collection(db, "users", uid, "sleepLogs");
  const q    = query(ref, orderBy("createdAt", "desc"));
  const snap = await getDocs(q);
  return snap.docs.slice(0, 7).map(d => ({ id: d.id, ...d.data() }));
}

// ─────────────────────────────────────────
// LUCID DREAMING
// ─────────────────────────────────────────

// logData: { date (YYYY-MM-DD), realityChecks, intention }
export async function saveLucidLog(uid, logData) {
  await setDoc(doc(db, "users", uid, "lucidLogs", logData.date), {
    ...logData,
    updatedAt: serverTimestamp()
  });
}

export async function getLucidLog(uid, date) {
  const snap = await getDoc(doc(db, "users", uid, "lucidLogs", date));
  return snap.exists() ? snap.data() : { date, realityChecks: 0, intention: '' };
}

export async function getLucidStreak(uid) {
  const ref  = collection(db, "users", uid, "lucidLogs");
  const q    = query(ref, orderBy("date", "desc"), limit(30));
  const snap = await getDocs(q);
  const logs = snap.docs.map(d => d.data());
  let streak = 0;
  const today = new Date().toISOString().slice(0, 10);
  let check   = today;
  for (const log of logs) {
    if (log.date === check && log.realityChecks > 0) {
      streak++;
      const d = new Date(check); d.setDate(d.getDate() - 1);
      check = d.toISOString().slice(0, 10);
    } else if (log.date < check) break;
  }
  return streak;
}

export async function getLucidDreams(uid) {
  const ref  = collection(db, "users", uid, "dreams");
  const snap = await getDocs(ref);
  return snap.docs.filter(d => d.data().lucid).map(d => ({ id: d.id, ...d.data() }));
}

// ─────────────────────────────────────────
// NIGHTMARE CHECK-INS
// ─────────────────────────────────────────

export async function saveNightmareCheckin(uid, date, hadNightmare) {
  await setDoc(doc(db, "users", uid, "nightmareCheckins", date), {
    date, hadNightmare, createdAt: serverTimestamp()
  });
}

export async function getTodayCheckin(uid) {
  const today = new Date().toISOString().slice(0, 10);
  const snap  = await getDoc(doc(db, "users", uid, "nightmareCheckins", today));
  return snap.exists() ? snap.data() : null;
}

export async function getNightmareCheckins(uid, days = 14) {
  const ref  = collection(db, "users", uid, "nightmareCheckins");
  const q    = query(ref, orderBy("date", "desc"), limit(days));
  const snap = await getDocs(q);
  return snap.docs.map(d => d.data());
}