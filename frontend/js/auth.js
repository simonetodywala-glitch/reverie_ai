// ─────────────────────────────────────────
// REVERIE — auth.js
// Firebase Authentication helpers
// Import this wherever you need login/signup/logout
// ─────────────────────────────────────────

import { app, saveUserProfile } from './firebase.js';
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

export const auth = getAuth(app);

// ─────────────────────────────────────────
// SIGN UP with email + password
// Also saves name + onboarding profile to Firestore
// ─────────────────────────────────────────
export async function signUp(name, email, password, profile = {}) {
  const cred = await createUserWithEmailAndPassword(auth, email, password);

  // Set display name in Firebase Auth
  await updateProfile(cred.user, { displayName: name });

  // Save full profile to Firestore
  await saveUserProfile(cred.user.uid, {
    name,
    email,
    chronotype: profile.chronotype || null,
    goal:       profile.goal       || null,
    wakeTime:   profile.wakeTime   || "07:00",
    createdAt:  new Date().toISOString()
  });

  return cred.user;
}

// ─────────────────────────────────────────
// LOG IN with email + password
// ─────────────────────────────────────────
export async function logIn(email, password) {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return cred.user;
}

// ─────────────────────────────────────────
// SIGN IN WITH GOOGLE
// ─────────────────────────────────────────
export async function signInWithGoogle() {
  const provider = new GoogleAuthProvider();
  const result   = await signInWithPopup(auth, provider);

  // Save basic profile to Firestore if it's a new user
  await saveUserProfile(result.user.uid, {
    name:  result.user.displayName,
    email: result.user.email,
  });

  return result.user;
}

// ─────────────────────────────────────────
// LOG OUT
// ─────────────────────────────────────────
export async function logOut() {
  await signOut(auth);
  window.location.href = '/pages/onboarding.html?signin=1';
}

// ─────────────────────────────────────────
// GET CURRENT USER
// Returns the logged-in user, or null if not logged in
// ─────────────────────────────────────────
export function getCurrentUser() {
  return auth.currentUser;
}

// ─────────────────────────────────────────
// REQUIRE AUTH
// Use this on any page that needs a logged-in user.
// Redirects to onboarding if not logged in.
// Usage: requireAuth(user => { /* use user.uid etc */ })
// ─────────────────────────────────────────
export function requireAuth(callback) {
  onAuthStateChanged(auth, user => {
    if (!user) {
      const wasOnboarded = localStorage.getItem('reverie_onboarded') === 'true';
      window.location.href = wasOnboarded
        ? '/pages/onboarding.html?signin=1'
        : '/pages/onboarding.html';
    } else {
      if (window._setReverieUser) window._setReverieUser(user);
      callback(user);
    }
  });
}