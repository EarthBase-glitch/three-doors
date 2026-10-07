# Notes for the owner

## 2026-10-07 — large backlog of unmerged `daily-update-*` branches, heavy duplication

`main` hasn't merged a daily-update PR since **2026-09-05** (the "Add copyright holder name to LICENSE" commit). Since then, roughly 20 more `daily-update-YYYY-MM-DD` branches have been pushed (2026-09-06 through 2026-10-05, several dates skipped) and none have been merged — they're all still open against the same stale `main`.

Because each day's session only ever sees what's already on `main`, and `main` never picked up any of that backlog, almost every one of those branches independently had the same idea: add another milestone to the Memories/Visions streak ladder, or add a second "lifetime count" ladder next to it. Concretely, across the unmerged branches I sampled:

- At least **six** separate branches add a new day-N milestone to the existing `VISION_MILESTONES`/`VISIONS` system (day 9, 40, 49, 60, 60, 60, 100, 100, 100 — several different branches picked day 100 independently).
- At least **four** separate branches add a second, lifetime-completion-count ladder alongside the streak one, under different names: "The Register," "Grace" / "The Fire Remembers" / "Past Lives" (09-23), "Echoes" (10-01 and 10-03 — two unrelated features sharing a name), and a `TOTAL_VISION_MILESTONES` lifetime track (10-05).
- One branch (2026-09-13) already noticed this exact problem and flagged it in its own changelog entry, and deliberately built something structurally different (a live, shared, population-based line) to sidestep it — worth reading before merging anything.

If several of these get merged as-is, you'll likely get duplicate/overlapping Memories content, naming collisions ("Echoes" means two different things), and possibly conflicting edits to `VISION_MILESTONES`/`VISIONS` that don't merge cleanly. Recommend: skim the backlog, pick the strongest version of each idea, close the rest, and merge `main` forward before the next daily session runs again — otherwise this keeps compounding.

Today's own addition (`daily-update-2026-10-07`, see CHANGELOG.md) was deliberately kept **off** that collision path — it's a one-time player *choice* on first task completion per realm, not another streak/count-gated milestone — so it shouldn't conflict with any of the above, but it was branched off the same stale `main`, so it will need a normal merge once you've cleared or merged some of the backlog.

No Firestore console changes needed for today's update — `firestore.rules` was not touched.
