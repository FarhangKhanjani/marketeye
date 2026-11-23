// Login and saved-search history, backed by Supabase (Auth + Postgres).
// Saved searches live in public.searches; row-level security lets each user see only their own rows.
import { SUPABASE_URL, SUPABASE_ANON_KEY, USERNAME_DOMAIN } from "./supabase-config.js";

const SDK = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/+esm";
export const configured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

let sb;
const ready = configured
  ? import(SDK).then(({ createClient }) => { sb = createClient(SUPABASE_URL, SUPABASE_ANON_KEY); })
  : Promise.resolve();

/** Calls cb(user|null) now and on every login/logout. */
export async function onUser(cb) {
  await ready;
  if (!configured) return cb(null);
  sb.auth.onAuthStateChange((_event, session) => cb(session?.user ?? null));
}

export const displayName = user => user.email.split("@")[0];

export async function login(username, password) {
  await ready;
  const name = username.trim().toLowerCase();
  const email = name.includes("@") ? name : `${name}@${USERNAME_DOMAIN}`;
  const { error } = await sb.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

export async function logout() { await ready; await sb.auth.signOut(); }

export async function saveSearch(s) {
  await ready;
  const { data, error } = await sb.from("searches").insert({
    fetched_at: s.fetched_at, settings: s.settings, dominance: s.dominance, pool: s.pool, excluded: s.excluded,
    longs: s.long, shorts: s.short, outliers: s.outliers,
  }).select("id").single();
  if (error) throw error;
  return data.id;
}

export async function listSearches() {
  await ready;
  const { data, error } = await sb.from("searches").select("*").order("saved_at", { ascending: false });
  if (error) throw error;
  return data.map(r => ({
    id: r.id, saved_at: new Date(r.saved_at), fetched_at: r.fetched_at, settings: r.settings,
    dominance: Number(r.dominance), pool: r.pool, excluded: r.excluded,
    long: r.longs, short: r.shorts, outliers: r.outliers,
  }));
}

export async function deleteSearch(id) {
  await ready;
  const { error } = await sb.from("searches").delete().eq("id", id);
  if (error) throw error;
}

export function friendlyError(e) {
  const code = e?.code || "";
  if (code === "invalid_credentials" || /invalid login credentials/i.test(e?.message || "")) return "Wrong username or password.";
  if (code === "over_request_rate_limit" || e?.status === 429) return "Too many attempts. Wait a minute and try again.";
  if (code === "42501") return "You don't have access to this. Try logging in again.";
  if (e instanceof TypeError) return "No connection. Check your internet and try again.";
  return e?.message || "Something went wrong.";
}

/** Only allow redirects back to our own pages. */
export function safeNext(param, fallback = "index.html") {
  return ["index.html", "history.html"].includes(param) ? param : fallback;
}
