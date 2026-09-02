# Three Doors

A door for Heaven, one for Hell, one to be Reincarnated. Sign in, choose,
build a character, and add to the shared lore for whichever realm you
land in.

## One-time setup (do this before it's live for real)

1. **Firebase config** — open `firebase-config.js` and replace the
   placeholder values with your project's real config: Firebase console →
   Project settings (gear icon) → *Your apps* → SDK setup and
   configuration. If you don't have a web app registered yet, click
   *Add app → Web* (`</>`) first.

2. **Firestore** — Firebase console → Build → Firestore Database →
   Create database, if you haven't already (test mode is fine to start).

3. **Security rules** — Firestore → Rules tab → replace the contents with
   everything in `firestore.rules` from this folder → Publish.

4. **Authentication (for the review queue)** — Firebase console → Build →
   Authentication → Get started → enable the **Email/Password**
   sign-in method → Users tab → Add user. Create exactly **one** account
   for yourself — this is the only account able to approve or reject lore
   submissions. Use a real password you don't reuse anywhere else, and
   don't share it with anyone (including in chat, ever).

## Publish to GitHub Pages

1. Create a new repository on GitHub.
2. On the repo page, use **Add file → Upload files** and drag in every
   file from this folder (`index.html`, `admin.html`, `firebase-config.js`,
   `firebase-adapter.js`, `firestore.rules`, `LICENSE`, `CONTRIBUTING.md`,
   `README.md`) — no command line needed.
3. Repository → Settings → Pages → Source: deploy from the `main` branch,
   root folder.
4. Your site goes live at `https://<your-username>.github.io/<repo-name>/`.
   That's the link to send anyone.

## Reviewing submitted lore

Visit `/admin.html` on your published site (e.g.
`https://<your-username>.github.io/<repo-name>/admin.html`) and sign in
with the account you created in step 4 above. Approve or reject anything
waiting — only approved entries appear on the live site, grouped under
whichever realm they were written for.

## How identity works here

There's no real login (no Google/Facebook/etc.) — visitors pick a name
and a passphrase, and the same pair on any device brings back their door
choice and character. It's intentionally lightweight, not verified
security; see the note on the sign-in screen itself.

## License

All rights reserved — see `LICENSE`. Code contributions are welcome via
pull request; see `CONTRIBUTING.md`.
