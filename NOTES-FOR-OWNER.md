# Notes for the owner

Manual Firebase console steps required by past daily updates. Newest first.

## 2026-10-20 — new Firestore collection: `echoes`

Today's three additions (Heaven's Ledger of Light, Hell's Confession Box,
Reincarnation's Fragments of the Last Life — see CHANGELOG.md) are backed
by a new Firestore collection, `echoes/{accountId}`, separate from the
existing `dailytasks`/`characters` collections on purpose (so this feature
can never collide with either of those docs' own full-document writes).

**Action needed:** paste the updated `firestore.rules` into the Firebase
console (Firestore → Rules) so the new collection is actually readable/
writable in production — same open-access shape as `votes`/`dailytasks`/
`characters` (no real per-account auth to gate on, matching the rest of
the app's "handle + passphrase" identity model). The new block added is:

```
match /echoes/{id} {
  allow read: if true;
  allow write: if true;
}
```

Until this is published, the three new screens will silently fail to save
(the app already handles that gracefully — a "couldn't save" message, not
a crash — but visitors won't be able to keep any Echoes until the rule is
live).
