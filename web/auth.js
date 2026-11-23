// Login and saved-search history, backed by Firebase Auth + Firestore.
// Saved searches live at users/{uid}/searches/{id}; firestore.rules lets each user see only their own.
import { firebaseConfig, USERNAME_DOMAIN } from "./firebase-config.js";

const SDK = "https://www.gstatic.com/firebasejs/10.12.2";
export const configured = Boolean(firebaseConfig.apiKey);

let fa, fs, auth, db;
const ready = configured ? (async () => {
  const [app, authMod, fsMod] = await Promise.all([
    import(`${SDK}/firebase-app.js`), import(`${SDK}/firebase-auth.js`), import(`${SDK}/firebase-firestore.js`)]);
  const fbApp = app.initializeApp(firebaseConfig);
  fa = authMod; fs = fsMod; auth = fa.getAuth(fbApp); db = fs.getFirestore(fbApp);
})() : Promise.resolve();

/** Calls cb(user|null) now and on every login/logout. */
export async function onUser(cb) {
  await ready;
  if (!configured) return cb(null);
  fa.onAuthStateChanged(auth, cb);
}

export const displayName = user => user.email.split("@")[0];

export async function login(username, password) {
  await ready;
  const name = username.trim().toLowerCase();
  const email = name.includes("@") ? name : `${name}@${USERNAME_DOMAIN}`;
  return fa.signInWithEmailAndPassword(auth, email, password);
}

export async function logout() { await ready; return fa.signOut(auth); }

const searches = () => fs.collection(db, "users", auth.currentUser.uid, "searches");

export async function saveSearch(snapshot) {
  await ready;
  const ref = await fs.addDoc(searches(), { ...snapshot, saved_at: fs.serverTimestamp() });
  return ref.id;
}

export async function listSearches() {
  await ready;
  const snap = await fs.getDocs(fs.query(searches(), fs.orderBy("saved_at", "desc")));
  return snap.docs.map(d => ({ id: d.id, ...d.data(), saved_at: d.data().saved_at?.toDate() ?? new Date() }));
}

export async function deleteSearch(id) { await ready; return fs.deleteDoc(fs.doc(searches(), id)); }

export function friendlyError(e) {
  const code = e?.code || "";
  if (["auth/invalid-credential", "auth/wrong-password", "auth/user-not-found", "auth/invalid-email"].includes(code))
    return "Wrong username or password.";
  if (code === "auth/too-many-requests") return "Too many attempts. Wait a minute and try again.";
  if (code === "auth/network-request-failed") return "No connection. Check your internet and try again.";
  if (code === "permission-denied") return "You don't have access to this. Try logging in again.";
  return e?.message || "Something went wrong.";
}

/** Only allow redirects back to our own pages. */
export function safeNext(param, fallback = "index.html") {
  return ["index.html", "history.html"].includes(param) ? param : fallback;
}
