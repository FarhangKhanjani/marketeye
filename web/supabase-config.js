// Supabase settings: Project Settings -> API (or the "Connect" button) in the Supabase dashboard.
// Use the Project URL and the anon / publishable key. Both are safe to publish:
// row-level security in supabase/schema.sql decides who can read or write what.
// Never put the service_role / secret key here.
// While url is empty, login and history are switched off and the site works as before.
export const SUPABASE_URL = "https://foxkkuresnfzakhdalxr.supabase.co";
export const SUPABASE_ANON_KEY = "sb_publishable_xVgx4jJubvazA0bKOwvwfQ_6ORDAJoc";

// Usernames are stored in Supabase Auth as <username>@<this domain>, e.g. admin -> admin@marketeye.app
export const USERNAME_DOMAIN = "marketeye.app";
