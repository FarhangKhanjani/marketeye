// Firebase web config. Paste the values from Firebase console -> Project settings -> Your apps -> Web app.
// These values are safe to publish: who can read or write data is controlled by firestore.rules.
// While apiKey is empty, login and history are switched off and the site works as before.
export const firebaseConfig = {
  apiKey: "",
  authDomain: "",
  projectId: "",
  appId: "",
};

// Usernames are stored in Firebase as <username>@<this domain>, e.g. admin -> admin@marketeye.app
export const USERNAME_DOMAIN = "marketeye.app";
