# Notes for the owner

Manual steps and heads-ups from automated daily updates that need a human. Newest first.

## 2026-11-16 — large backlog of unmerged `daily-update-*` PRs, several redundant

No `firestore.rules` change today — nothing to paste into the Firebase console for this update.

Separately, worth knowing: there are roughly twenty open `daily-update-YYYY-MM-DD` branches/PRs sitting unmerged against `main`, going back to **2026-10-27**. None of them have been merged, so none of their content is live, and each day's run has been working from the same un-updated `main` — unable to see what previous days already proposed.

The practical effect: at least **fifteen of those branches independently added their own "day 100" (or day 60/day 14) Memories-vision milestone**, each with different title/text but the same underlying idea, because each run's `CHANGELOG.md` only reflected work already merged (last merged story content is from 2026-09-02/09-03). This wasn't a mistake in any single run — it's a consequence of the review queue growing faster than it's been reviewed. If several of these get merged together later, expect `index.html` merge conflicts right at the `VISION_MILESTONES`/`VISIONS` insertion points, and likely duplicate/overlapping "day 100" content even after conflicts are resolved by hand.

Suggested options, your call:
- Pick your favorite one or two of the day-100/60/14 PRs, merge those, and close the rest (with a thank-you comment, they're genuinely fine work, just redundant with each other).
- Or close all of the backlog and let the story ladder pick up fresh from whatever's merged next.
- Either way, merging (or closing) the backlog regularly will let future daily runs build on each other instead of re-discovering the same "extend the ladder" idea.

Today's change (2026-11-16) adds a **day-1** vision per realm instead — deliberately different from the backlog so it won't collide with any of those pending PRs, and it fills a real gap (no visitor sees any story before a 3-day streak today). See `CHANGELOG.md` for details.
