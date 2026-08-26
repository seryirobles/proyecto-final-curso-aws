# Gaps and Resolutions — Reasoning Log

> Companion to `requirements.md`. Every ambiguity or hole found between the user
> stories and the requirements gets a `G-xx` entry here with the decision taken
> and why. Entries **G-01 to G-08 and G-13** record decisions that were already
> embedded in the original requirements (this file re-documents them). Entries
> **G-03, G-09 to G-12, G-14 to G-27** come from the coverage review of
> 2026-07-03 (see `coverage_analysis.md`). Entries **G-28 to G-35** come from
> stakeholder answers received later the same day, which also **added three new
> user stories** — admin user removal, next-week planning, and shopping-item
> check-off — shifting `US#` numbering once more. All `US#` citations below,
> including in the older entries, have been updated to the **current, final**
> numbering in `app_user_stories.md` (27 stories). Entries **G-36 to G-41**
> record the stakeholder's confirmation, later the same day, that the remaining
> six working assumptions in `gaps_pending_stakeholders.md` are final as
> written. Entries **G-42 to G-51** come from a **post-integration re-scan**
> (same day) focused on interactions created by the newly added scope
> (next-week planning, user removal, check-off, search, unit handling); that
> scan also raised one new business question, **PEND-14**, resolved and then
> refined by the stakeholder on **2026-07-04** — see entries **G-52 and G-53**
> in Part F. Entries **G-54 to G-61** come from a **second post-integration
> re-scan** (2026-07-04) focused on the interactions created by the
> shopping-list decisions and the two-live-week model; that scan raised one
> new business question, **PEND-15** (accessibility target), answered by the
> stakeholder the same day (browser defaults only — G-62). Entries **G-62 to
> G-67** come from the final exhaustive sweep of 2026-07-04 (Part H), which
> also records what was examined and deliberately rejected as beyond-MVP. No
> business questions remain open.

---

## Part A — Decisions already reflected in the original requirements

### G-01 · How many admin accounts, and how is the first one created?
- **Gap:** US1/US2 assume an admin exists, but with self-registration forbidden (US2, US5) nothing says how admins come into existence or how many there are.
- **Decision:** Provision exactly one bootstrap admin at deployment; the data model supports multiple admins.
- **Reasoning:** A bootstrap account is the only way to satisfy "no registration" while still having a first admin. Supporting multiple admins costs nothing and enables admins to reset each other, which matters because nobody can change their own password (US2). Final admin count is a business call → PEND-06.
- **Requirements:** FR-AUTH-07.

### G-02 · What exactly is the "current week", and what happens when it ends?
- **Gap:** US7 says "current week" and US25 says past menus are kept, but no story defines the week boundary or the transition.
- **Decision:** ISO week (Monday–Sunday) in Europe/Madrid; at rollover the ending week is archived automatically and becomes read-only.
- **Reasoning:** The app is in Castilian Spanish for a household-style group, so Spanish local time is the natural clock. An unambiguous boundary is required for archiving (US25), shopping-list scope (US21–23), and the real-time shared state (US19) — every user must agree on which week is "current". Automatic archiving is the only option compatible with "keep a record of all past weeks" without relying on someone remembering to archive. This resolution was later extended to cover a second live week (next week) — see G-28.
- **Requirements:** FR-MENU-02, FR-ARCH-02.

### G-04 · How do manual and auto-generated shopping items coexist, and which meals feed the list?
- **Gap:** US22 (manual add/edit/remove) and US23 (auto-add from the menu) can destroy each other's data if naively combined; the stories also don't say whether candidates or definitives drive the auto items.
- **Decision:** Auto and manual items are distinguishable; re-syncing auto items never deletes manual ones; the list derives from **definitive** meals only.
- **Reasoning:** Deriving from candidates would list ingredients for meals that will never be cooked (each slot can hold many candidates but only one definitive). Losing a user's manually added items on re-sync would make US22 pointless.
- **Requirements:** FR-SHOP-03, FR-SHOP-04, FR-SHOP-05.

### G-05 · What happens to menus when a library recipe is edited or deleted?
- **Gap:** Recipes can be added to menus from the library (US10) and the library is freely editable by everyone (US18). If menus point at live library entries, edits/deletions retroactively rewrite current and archived weeks.
- **Decision:** Menus store a **snapshot** of the recipe at the moment it is added.
- **Reasoning:** US25 requires a faithful record of past weeks; a shared editable library makes live references unstable. Snapshots decouple the two at the cost of some duplication, which is trivial for text-sized data.
- **Requirements:** FR-CAND-07.

### G-06 · What does "edit the rules only for the current week" mean?
- **Gap:** US13 offers editing the general rules "only for the current week", but US26 defines the rules as shared and affecting every week — two readings: temporarily mutate the shared rules, or override per generation run.
- **Decision:** A per-run override passed to that single generation; shared rules are untouched.
- **Reasoning:** Temporarily mutating shared state is racy with real-time collaboration (US19) and needs an "expiry" mechanism nobody asked for. A per-run override is side-effect-free and matches the story's intent ("only for the current week").
- **Requirements:** FR-AI-05, FR-RULE-05.

### G-07 · How are concurrent edits by several users resolved?
- **Gap:** US19 demands real-time collaboration but no story defines conflict behaviour (two users editing the same candidate, promoting different definitives, editing rules simultaneously).
- **Decision:** Last-write-wins, with author attribution and real-time broadcast.
- **Reasoning:** The user base is a small, trusting group (household/team). Operational transforms or CRDTs would be heavy machinery for a menu planner; attribution plus instant broadcast makes any overwrite immediately visible and fixable. Attribution is needed anyway for US16.
- **Requirements:** FR-RT-02.

### G-08 · How is a locked-out admin recovered?
- **Gap:** Admins cannot change their own passwords (US2) and with a single admin nobody can reset it.
- **Decision:** Re-seed the bootstrap admin credential from its IaC-managed secret.
- **Reasoning:** Keeps recovery out of the application (no backdoor endpoint to secure) and inside the operational plane, which is already trusted (Terraform + Secrets Manager, NFR-SEC-02).
- **Requirements:** FR-AUTH-08.

### G-13 · How long are past weeks kept, and at what cost?
- **Gap:** US25 says "access them any time", which naively means unbounded hot storage forever.
- **Decision:** Indefinite retention; a scheduled job moves records older than ~3 months to cold storage (e.g. S3 Glacier); the UI shows a "restoring…" state for cold records.
- **Reasoning:** Honors "any time" literally while respecting the project's cost constraints (NFR-FIN-02). Old menus are read rarely; minutes-to-hours retrieval is an acceptable trade-off. Threshold confirmation → PEND-08.
- **Requirements:** FR-ARCH-03.

---

## Part B — Gaps found in the 2026-07-03 coverage review

### G-03 · Story numbering drift; US3 covered only implicitly
- **Gap:** `requirements.md` was written against an earlier story list. A story about the admin resetting a user's password had been inserted, and a story about setting your own password at first login/after reset had been appended, so every `US#` from that point on pointed at the wrong story, and the reset story itself had no explicit trace — the admin-view requirement mentioned "change/reset" but cited only the user-management story.
- **Decision:** Renumber all references to the current `app_user_stories.md` line order; trace the admin-view requirement to the reset story explicitly.
- **Reasoning:** A traceability matrix that points at the wrong stories is worse than none — it certifies coverage that may not exist. This drift is exactly how the set-password story went unnoticed. (Note: after this fix was made, three more stories were added the same day per stakeholder answers — see the header note above — requiring a second renumbering pass, already folded into the citations throughout this file.)
- **Requirements:** whole-document renumbering; FR-AUTH-05.

### G-09 · US27 (set password at first login / after reset) was uncovered — and contradicted
- **Gap:** No requirement implemented the set-password story. Worse, the old FR-AUTH-04 ("neither admins nor users shall be able to change their own password") outright forbade it.
- **Decision:** Amend FR-AUTH-04 to carve out exactly one exception — the mandatory set-password step at login — and add FR-AUTH-10 forcing that step on first login and after an admin reset, for both roles.
- **Reasoning:** US27 explicitly includes admins ("as a user or an admin"), so the flow must apply to both roles. Making the step *mandatory* (not optional) is the reading that keeps FR-AUTH-04 meaningful: the user never operates the app on an admin-known password, and there is still no free-form "change my password" feature — the stories' restriction stays intact.
- **Requirements:** FR-AUTH-04 (amended), FR-AUTH-10.

### G-10 · Lifecycle of admin-assigned passwords
- **Gap:** US3/US27 imply an admin sets or resets a password that the account holder then replaces, but nothing defined that password's validity or what happens to live sessions after a reset.
- **Decision:** Admin-assigned passwords are temporary — valid only to reach the set-password step, never to enter the app. A reset invalidates all active sessions of the account.
- **Reasoning:** The admin knows the temporary password; if it granted full access, the admin could impersonate users, undermining the definitive-meal attribution (US16) and edit attribution (G-07). Session invalidation is the reason resets exist: if a reset doesn't kick out whoever holds the session, it doesn't actually recover a possibly-compromised account.
- **Requirements:** FR-AUTH-11.

### G-11 · The admin cannot manage users they cannot see
- **Gap:** US1 says "create and manage users", and every management action (rename, reset) targets an existing account — but no requirement gave the admin a list of accounts to act on.
- **Decision:** The admin view shows all accounts with username, role, and pending set-password status, as the entry point for the FR-AUTH-05 actions.
- **Reasoning:** Pure UX necessity — the story is unimplementable without it. Showing the pending set-password status lets the admin verify a reset "took" and help users stuck at first login. (Later extended to also launch the removal action — see G-29.)
- **Requirements:** FR-AUTH-12.

### G-12 · Login brute-force protection unspecified
- **Gap:** The app is internet-exposed, has no MFA and no self-service recovery, and passwords are the single factor (US2/US5) — yet no requirement protected the login from credential guessing.
- **Decision:** Rate limiting and/or progressive lockout on repeated failures, plus a generic error message that doesn't disclose whether the username exists.
- **Reasoning:** With a tiny, known user base, username enumeration plus unlimited guessing is the entire attack surface. This is a security-hygiene consequence of the chosen auth model, not a new feature.
- **Requirements:** NFR-SEC-04.

### G-14 · Recipe detail only specified from the week-menu view
- **Gap:** US9 ("click a meal and see the detailed recipe") is phrased from the week menu, but meals also appear in the summary (US16), the library (US18), and archived weeks (US25). Nothing said the detail view works there too.
- **Decision:** The detail view opens from every place a meal is displayed.
- **Reasoning:** Users don't distinguish "a meal in the menu" from "a meal in the summary"; a meal you can see but not open reads as a bug. This generalizes the story's intent without adding any new capability.
- **Requirements:** FR-MENU-05.

### G-15 · State of the new week at rollover
- **Gap:** G-02 defined *when* the week flips and that the old one is archived, but not what the incoming week looks like — empty, or pre-populated from the rules (pinned meals, etc.)?
- **Decision:** The new current week starts with all slots empty; rules materialize only through a generation run (FR-AI-11) or manual planning.
- **Reasoning:** US26's rules are defined as *generation* instructions, and US13 requires a confirmation prompt before rules are applied — silently pre-populating at midnight would apply rules with no confirmation and would surprise users with meals nobody proposed. Starting empty keeps a single, predictable entry point for rules. (Superseded in detail, not in principle, once next-week planning was added — see G-28: the "new current week" is now usually the former next week, which may already have content from deliberate planning, not from silent pre-population.)
- **Requirements:** FR-MENU-06.

### G-16 · A definitive selection could not be undone
- **Gap:** US15 covers promoting a candidate to definitive and FR-CAND-05 covers *replacing* it with another candidate — but there was no way to simply revert a slot to "nothing decided yet".
- **Decision:** Users can clear the definitive selection, returning the slot's meals to candidate status.
- **Reasoning:** Plans change ("we're eating out Friday"). Without a clear action, users would fabricate workarounds (fake candidates, deleting the meal entirely), corrupting the summary (US16) and the shopping list (US23). This is the undo of an action the stories already define, not a new feature.
- **Requirements:** FR-CAND-08.

### G-17 · AI-generated recipes landed directly in the plan with no review step
- **Gap:** US17 says "generate a new meal with AI", but the requirements had the result saved immediately as a candidate/library entry. LLM output quality varies; a bad recipe would pollute the shared, real-time-broadcast plan.
- **Decision:** Single-recipe generation shows a preview with accept / discard / regenerate (optionally adjusting specs); nothing is saved until accepted. Regenerations count against the AI caps.
- **Reasoning:** "Generating a meal" implies the user gets the meal they wanted — an accept step is the minimal UX that delivers that with a nondeterministic generator, and it avoids broadcasting rejects to every user (US19). Counting regenerations keeps NFR-AI-01's cost cap honest. Whole-week generation (US12) deliberately stays fire-and-forget: its results are *candidates* by design, so the review step is the candidate-selection flow itself (US15).
- **Requirements:** FR-AI-10.

### G-18 · Whole-week generation: which slots, and what about existing content?
- **Gap:** US12 says AI fills "the whole week", but the week may already contain candidates and definitives. Overwrite? Skip? Duplicate?
- **Decision:** Generation targets every slot not disabled by the rules, *adds* candidates without removing existing candidates or definitives, and pinned slots receive their pinned library meal as the candidate.
- **Reasoning:** US12 explicitly says generated meals arrive "as candidates" — the candidate model exists precisely so proposals accumulate until someone chooses (US15). Deleting other users' work from a bulk action would violate the collaborative model and be unrecoverable. Rules integration follows US26's own definitions (pinning, disabled days).
- **Requirements:** FR-AI-11.

### G-19 · AI progress and failure behaviour was invisible
- **Gap:** AI calls take seconds (single recipe) to a minute-plus (14 slots). FR-AI-09 already said one slot's failure doesn't abort the rest — but nothing said how the user learns about progress or failures.
- **Decision:** Loading/progress states for all AI operations (per slot for whole-week runs); failures surfaced per slot with a retry option and a friendly Spanish message; partial results kept.
- **Reasoning:** Without a progress state users re-click (mitigated but not excused by FR-AI-08's idempotency) or assume the app is broken. Per-slot retry is the natural complement of per-slot independence: pay only for the failed slot, not the whole week again (NFR-AI-01).
- **Requirements:** FR-AI-12.

### G-20 · Nothing kept the rule set satisfiable
- **Gap:** US26's rule types can contradict each other: ingredient-category counts exceeding the 14 weekly slots (fewer, after disabled days), or a meal pinned on a disabled day. Also, deleting a library recipe (US18) that a pin rule references left the rule dangling. An unsatisfiable rule set makes every generation run (US12) fail or silently disobey rules.
- **Decision:** Constrain the dropdown options so contradictory combinations cannot be composed; on deleting a pinned recipe, warn and remove the affected rule upon confirmation.
- **Reasoning:** US26 already mandates dropdown-only editing — constraining the option sets is the same mechanism doing double duty as validation, with no new UI. Warn-and-remove (rather than blocking the delete) keeps library management (US18) unobstructed while never leaving a broken rule behind silently.
- **Requirements:** FR-RULE-07.

### G-21 · Shopping re-sync trigger and edited auto-items were undefined
- **Gap:** G-04 established that auto and manual items coexist, but not *when* re-sync happens (button? schedule? event?) nor what happens to an auto item the user has edited (US22 allows editing any item) when re-sync recomputes it.
- **Decision:** Re-sync runs automatically whenever the week's definitive meals change; auto items with user-edited name or quantity become manual overrides and are preserved.
- **Reasoning:** A manual sync button invites stale lists — the failure mode US23 exists to prevent. Overwriting a user's deliberate edit ("we already have rice") on the next definitive change would make US22's edit feature unreliable; preserve-on-edit is the standard resolution (same principle that protects manual items in G-04). The same preserve-on-edit principle was later extended to checked/bought state — see G-32.
- **Requirements:** FR-SHOP-06.
- **Superseded (2026-07-04):** the *automatic* trigger was replaced by an explicit **button press** when the stakeholder resolved PEND-14 — see G-52. The preserve-on-edit principle stands unchanged.

### G-22 · Real-time connection loss was unhandled
- **Gap:** US19 promises real-time visibility of others' changes, but websocket-style connections drop routinely (mobile, US6). A silently dead connection turns "real time" into "confidently stale" — worse than no real-time at all, since users trust what they see.
- **Decision:** The UI indicates connection loss, reconnects automatically, and re-synchronizes state on reconnection.
- **Reasoning:** The dangerous state is not being disconnected, it is *not knowing* you are. Re-sync on reconnect is required because events missed while offline are otherwise lost forever, permanently forking what two users see.
- **Requirements:** FR-RT-03.

### G-23 · "In Spanish" covered the UI but not messages and formats
- **Gap:** FR-UX-01 covered UI copy and FR-AI-07 covered AI output, but validation errors, system/error messages, and date & number formats (day names in the menu, quantities in the shopping list) were unspecified — the classic leak where server errors surface in English.
- **Decision:** All texts of every origin, plus date/number formatting, follow es-ES conventions.
- **Reasoning:** US20 says "the app" is in Castilian Spanish, not "the labels". Error moments are when users most need to understand what happened; a Monday-to-Sunday menu grid with English day names or `1.5 cups` quantities visibly breaks the story.
- **Requirements:** FR-UX-03.

### G-24 · No confirmation on destructive actions
- **Gap:** The stories grant broad delete/replace powers (candidates US10, library recipes US18, shopping items US22, rules US26, replacing a definitive US15, and now removing a user US4) in a *shared* workspace with last-write-wins and no undo (G-07) — one misclick destroys another user's work, permanently.
- **Decision:** Destructive actions require explicit confirmation.
- **Reasoning:** Confirmation is the cheapest possible substitute for the undo system the MVP doesn't have. The cost (one extra click on rare actions) is trivially outweighed in a multi-user setting where the data you delete is usually someone else's.
- **Requirements:** FR-UX-04.

### G-25 · Empty and loading states unspecified
- **Gap:** Day one of the app — and every Monday (G-15) — presents an empty library, an empty week, and an empty shopping list. Unspecified empty states typically render as blank screens indistinguishable from loading failures.
- **Decision:** Every view defines an empty state with guidance toward the relevant action, and loading states for slow operations.
- **Reasoning:** The app's weekly cycle makes "empty" a recurring, first-class state, not an edge case. Guidance ("no candidates yet — add one or generate the week") is what connects the stories' features to a user staring at a blank Monday.
- **Requirements:** FR-UX-05.

### G-26 · "Save to library" duplicate behaviour undefined
- **Gap:** US11 saves a menu meal to the library, but the meal may itself have *come* from the library (possibly edited since, thanks to snapshots, G-05). Does saving create a duplicate, update the original, or get blocked?
- **Decision:** Always create a new library entry from the snapshot; warn when a same-name recipe already exists.
- **Reasoning:** Updating the original would silently overwrite a shared recipe other users rely on — the exact hazard G-05 exists to prevent, in reverse. Blocking would lose legitimately diverged versions. Create-plus-warning keeps the operation predictable and surfaces the duplication for the user to resolve (e.g. renaming), using the edit/delete tools US18 already provides.
- **Requirements:** FR-CAND-06 (amended).

### G-27 · No way to navigate the archive was specified
- **Gap:** US25 requires past weeks to be "accessible any time", and FR-ARCH-01..03 covered persistence and retention — but no requirement described how a user *finds* a past week.
- **Decision:** A reverse-chronological list/selector of archived weeks.
- **Reasoning:** Storage without navigation doesn't satisfy "access them any time". Reverse-chronological matches the dominant use case (recent weeks: "what did we cook last week?") and needs no search machinery for the MVP.
- **Requirements:** FR-ARCH-04.

---

## Part C — Stakeholder decisions (2026-07-03, second pass)

These entries resolve six of the seven `PEND` items raised in Part B by adding
new scope the stakeholder explicitly requested. They added three new user
stories, which is why every `US#` above was renumbered a second time (see the
header note).

### G-28 · Planning ahead: a second live week (resolves PEND-07)
- **Gap:** The stories only covered the current week (US7) and the past (US25); nothing let users plan ahead. This mattered in practice because the shopping list (US21–23) is only useful if it's ready *before* the week it's for begins — under a "current week only" model, Sunday's shopping trip could only ever be for a week already half over.
- **Decision:** Introduce a second live week, "next week," with **identical functionality** to the current week (candidates, definitive selection, AI generation, rules, summary). At rollover, the ending current week is archived, the former next week becomes the new current week (carrying over its content), and a fresh, empty next week is initialized.
- **Reasoning:** Mirrors the real household workflow this app is built for — you plan and shop on the weekend for the week ahead. Reusing the exact same mechanics (rather than inventing a separate "draft" concept) means no second data model or second UI for users to learn: everything in Sections 4, 6, 7 and 8 already generalizes to "a live week" with no semantic change. Carrying next week's content forward at rollover (rather than discarding it or re-generating) preserves the planning effort users already invested, consistent with the non-destructive stance taken for whole-week generation (G-18).
- **Requirements:** FR-MENU-01, FR-MENU-07 (new); FR-MENU-06, FR-SUM-01, FR-SHOP-01, FR-SHOP-05, FR-AI-03, FR-AI-04, FR-AI-11, FR-RT-01 (amended).

### G-29 · Removing a user, and what happens to their content (resolves PEND-09)
- **Gap:** US1 said the admin can "manage" users but didn't say whether that includes removal, and if it does, the app has no concept of orphaned content: candidates, library recipes, definitive-meal promotions, rule edits and shopping items are all attributed to a user (FR-SUM-02, FR-RULE-06, FR-RT-02) — content authored by a since-removed account would either dangle or force a deletion cascade that destroys other users' shared work.
- **Decision:** Admins can remove a user. All content that user authored is **kept**, but its attribution is replaced with a generic **"unknown user"** placeholder. Removal invalidates the account's active sessions immediately, mirroring the reset behavior in G-10.
- **Reasoning:** Deleting a departed member's recipes, candidates and rule edits would be destructive to a *shared, collaborative* dataset that other users still rely on — directly contradicting the non-destructive stance already taken for bulk AI generation (G-18) and for shopping re-sync (G-04, G-21). The alternative of leaving the stale username visibly attached forever was rejected because it makes a later account that reuses the same username ambiguous with the removed one's history; a generic placeholder sidesteps that entirely, at no cost since usernames are not guaranteed unique over time once an account is gone.
- **Requirements:** FR-AUTH-12 (amended), FR-AUTH-13, FR-AUTH-14, FR-SUM-03 (new).

### G-30 · Password policy (resolves half of PEND-05)
- **Gap:** FR-AUTH-10/-11 mandate a set-password step but never said what makes a password acceptable — length, character rules, expiry.
- **Decision:** Align with **NIST SP 800-63B**: minimum length 10 characters (supporting up to at least 64 without truncation), no mandatory character-composition rules (no forced uppercase/digit/symbol mix), no forced periodic rotation, and rejection of passwords found on a common/breached-password blocklist.
- **Reasoning:** NIST 800-63B is the current industry baseline, explicitly superseding the older complexity-mandate model, which research has shown pushes users toward predictable, easily-guessed patterns (e.g. `Password1!`, then `Password2!` at the next forced rotation). Given the app has no self-service password change (FR-AUTH-04) and resets are rare, admin-driven events, forced rotation adds user friction without a matching security benefit; a breach/common-password blocklist check is the control that actually stops the realistic attack (credential stuffing with previously-leaked passwords), which composition rules do not.
- **Requirements:** FR-AUTH-15.

### G-31 · Session lifetime (resolves the other half of PEND-05)
- **Gap:** FR-AUTH-09 required "authenticated sessions" and a logout action, but no session duration was ever specified.
- **Decision:** Sessions expire after 12 hours of inactivity or 30 days absolute lifetime, whichever comes first.
- **Reasoning:** A 12-hour idle timeout comfortably spans a single planning/shopping session (including working across lunch and dinner without re-login) while ensuring a shared or public device doesn't stay authenticated indefinitely once unused. The 30-day absolute cap bounds the damage window of a stolen session token regardless of activity, which matters more here than in a typical app because there is no self-service password change to let a user react to a suspected compromise (FR-AUTH-04) — an admin-driven reset (G-10) is the only recovery path, so sessions shouldn't be allowed to persist indefinitely on activity alone.
- **Requirements:** FR-AUTH-16.

### G-32 · Shopping-list check-off (resolves PEND-10)
- **Gap:** US21–23 (view, edit, auto-add) never covered marking an item as bought, despite that being the primary interaction with a shopping list while actually shopping. The stakeholder specified concrete UI behavior: checked items move to their own section below the unchecked ones and appear greyed out, and can be unchecked again.
- **Decision:** Items are checkable/uncheckable; checked items render in a separate section below all unchecked items, greyed out; check state is preserved across the automatic re-sync introduced in G-21/FR-SHOP-06.
- **Reasoning:** The below/greyed-out layout matches the mental model users already have from other grocery-list apps — visible progress, without checked items cluttering the still-to-buy list. Preserving check state across re-sync follows the exact same principle already established for manually-edited items (G-04, G-21): a re-sync recomputes *quantities*, it must never silently undo a user's real-world action (having already bought the item) — otherwise, a re-sync mid-week (triggered by any change to the week's definitive meals) would make finished shopping trips reappear as pending.
- **Requirements:** FR-SHOP-07, FR-SHOP-08.

### G-33 · Browser/device support matrix (resolves PEND-11)
- **Gap:** FR-UX-02 required "a responsive website" for desktop and mobile but named no browsers, leaving QA scope undefined.
- **Decision:** Support current major versions of Chrome, Firefox, Edge, Safari, and Chromium-based browsers such as Brave, across Windows/macOS/Linux desktop and Android/iOS mobile.
- **Reasoning:** Naming engines (Blink, Gecko, WebKit) rather than every rebadged Chromium browser individually keeps the requirement honest about what's actually being tested. The stakeholder specifically called out Safari and Brave, which are exactly the two likely sources of divergence in practice — Safari/WebKit has stricter storage and PWA/notification limits that can silently break real-time sync (FR-RT-01/-03) or session persistence (FR-AUTH-16), and Brave's aggressive default tracker/script blocking can interfere with the websocket-style connections real-time collaboration depends on — so both are named explicitly rather than left implicit under "Chromium-based."
- **Requirements:** FR-UX-02 (amended).

### G-34 · Library search and filtering (resolves PEND-12)
- **Gap:** US18 says users "see all of the recipes added to the library," with unlimited add rights for every user and no cap on growth — at any real scale, "see all" degenerates into an unusable, unordered scroll.
- **Decision:** Add search by recipe name and filtering by cuisine and/or difficulty.
- **Reasoning:** This is UX support for a capability the stories already grant (viewing and using the shared library), not new product scope — "seeing all recipes" stops meaning anything once the count exceeds what fits on a screen. Cuisine and difficulty require no new data since library recipes already store them (FR-LIB-03) for AI-generation purposes; reusing them for filtering is free.
- **Requirements:** FR-LIB-04.
- **Amended by G-68:** the cuisine/difficulty **filters** are removed with the attributes themselves. Search by recipe name survives and remains the answer to this gap.

### G-35 · Expected scale confirmed (closes PEND-13)
- **Gap:** Real-time fan-out (FR-RT-01), the AI cost cap (NFR-AI-01), and infrastructure sizing (NFR-FIN-02) all depend on how many users the app serves.
- **Decision:** The household/small-team scale assumption (~2–10 users) already used throughout the requirements is confirmed; no change to any requirement.
- **Reasoning:** Recorded here purely for traceability — this closes the open question without altering scope, cost caps, or architecture.
- **Requirements:** none (confirms the existing basis for NFR-AI-01, NFR-FIN-02).

---

## Part D — Remaining stakeholder confirmations (2026-07-03, third pass)

The stakeholder confirmed the last six open items in
`gaps_pending_stakeholders.md` as final, exactly as the working assumption
already documented them. No new requirements were needed — these entries exist
so the confirmation is traceable and future readers don't mistake the
remaining `PEND-xx` references in `requirements.md` for open questions.

### G-36 · "Healthy and balanced" definition confirmed (closes PEND-01)
- **Gap:** FR-AI-06 defined "balanced/healthy" only qualitatively (vary protein sources) plus enforcement through the general rules' ingredient-category counts, leaving open whether a stricter, medically-grounded definition (calories, allergies, dietary constraints) was wanted.
- **Decision:** The qualitative-prompt-plus-rules approach is confirmed as final; no medical/nutritional model is in scope.
- **Reasoning:** A medically-grounded definition would require nutritional data per ingredient, a computation engine, and a "non-medical" liability framing far beyond a household meal planner. The general rules (ingredient-category counts, US26) already give users direct control over the dimension they actually experience as "balance" (not eating meat five nights running), without pretending the app understands nutrition.
- **Requirements:** FR-AI-06 (unchanged).

### G-37 · Rule-editing governance confirmed (closes PEND-02)
- **Gap:** FR-RULE-06 let any user edit the shared general rules with no approval step, which was flagged as a possible governance gap (e.g., should one user be able to silently loosen another's dietary constraint?).
- **Decision:** Free-for-all editing, with attribution and real-time broadcast, is confirmed as final — no owner/approval role.
- **Reasoning:** Consistent with the collaboration model already adopted everywhere else in the app (last-write-wins with attribution, G-07): the group is small and trusting, and attribution plus instant visibility (everyone sees a rule change the moment it happens) is the same safety net already relied on for candidates and the library.
- **Requirements:** FR-RULE-06 (unchanged).

### G-38 · AI cost cap confirmed (closes PEND-03)
- **Gap:** NFR-AI-01 set a €50/month AI sub-budget but left the exact per-user daily generation cap unset, pending confirmation of the €50 figure itself.
- **Decision:** €50/month is confirmed as the AI cost cap. The exact per-user daily generation number is not fixed here — it is an engineering calculation (€50 ÷ actual provider price-per-generation ÷ days in month ÷ number of users) to be performed once the AI provider and model are chosen at implementation time, not a further business decision.
- **Reasoning:** The euro figure is the business decision (what the group is willing to spend); the per-user daily count is a derived, mechanical consequence of that figure and a technical fact (provider pricing) that doesn't exist yet. Closing the business question doesn't require pre-computing an engineering constant that will be recalculated the moment a model/provider is picked.
- **Requirements:** NFR-AI-01 (Source updated to drop the open `PEND-03` marker).

### G-39 · Shopping-list unit approach confirmed (closes PEND-04)
- **Gap:** FR-SHOP-03 used a "fixed unit list, no cross-unit conversion" approach without enumerating the actual units (g, kg, ml, l, units, …).
- **Decision:** The fixed-list-no-conversion approach is confirmed as final. The literal enumeration of units is left as an implementation detail (a static config list), not a further business decision.
- **Reasoning:** The business-relevant choice was *scope* — whether the app should do unit conversion at all (rejected, MVP) — not which specific unit strings appear in a dropdown, which is freely revisable in code without affecting the user-facing behavior described in US23.
- **Requirements:** FR-SHOP-03 (Source updated to drop the open `PEND-04` marker).

### G-40 · Admin-account bootstrap and recovery confirmed (closes PEND-06)
- **Gap:** FR-AUTH-07/-08 assumed a single bootstrap admin (with multi-admin support) and IaC-secret re-seeding for recovery, pending confirmation this was an acceptable operational model.
- **Decision:** Confirmed as final, unchanged.
- **Reasoning:** No new information changes the reasoning already given in G-01/G-08 — recorded here purely to close the loop.
- **Requirements:** FR-AUTH-07, FR-AUTH-08 (unchanged; Source updated to drop the open `PEND-06` marker).

### G-41 · Archive retention policy confirmed (closes PEND-08)
- **Gap:** FR-ARCH-03 set indefinite retention with cold storage after ~3 months and a "restoring…" UI state for cold records, pending confirmation of the threshold and the retrieval-delay trade-off.
- **Decision:** Confirmed as final, unchanged.
- **Reasoning:** No new information changes the reasoning already given in G-13 — recorded here purely to close the loop.
- **Requirements:** FR-ARCH-03 (unchanged; Source updated to drop the open `PEND-08` marker).

---

## Part E — Post-integration re-scan (2026-07-03, fourth pass)

With all stakeholder scope merged, the requirement set was re-scanned end to
end, looking specifically for **interactions between the newly added features**
(next-week planning, user removal, shopping check-off, library search, the
password/session policy) **and the pre-existing requirements**. Ten gaps were
found and resolved; one new business question (PEND-14) was raised.

### G-42 · Username uniqueness was never required
- **Gap:** Authentication is by username (FR-AUTH-02) and admins can rename accounts (FR-AUTH-05), yet no requirement made usernames unique — duplicate usernames make login resolution impossible. User removal (G-29) sharpened the question: may a removed account's username be reused?
- **Decision:** Usernames are unique **among active accounts**, validated on creation and rename; a removed account's username may be reused.
- **Reasoning:** Uniqueness among active accounts is the minimum for username login to function at all. Allowing reuse after removal is safe *because of* the decision already taken in G-29 — reattribution to "unknown user" was chosen precisely so no historical content points at the old username; forbidding reuse would forfeit that benefit for nothing.
- **Requirements:** FR-AUTH-17.

### G-43 · Multiple admins are supported but impossible to create — and undefined to remove
- **Gap:** FR-AUTH-07 supports multiple admins "so they can reset each other," but no mechanism creates a second admin: the admin view is restricted to *user* management (FR-AUTH-05, US1 "and nothing else"), and self-registration is forbidden. Likewise undefined: whether "reset each other" is actually reachable in the UI, and whether the new removal feature (FR-AUTH-13) applies to admin accounts — removing the last admin would lock user management entirely.
- **Decision:** Admin accounts are provisioned only via IaC (the same trusted plane as the bootstrap admin and its recovery, G-01/G-08); the admin view additionally allows resetting **another** admin's password (never one's own); admin accounts cannot be removed through the application.
- **Reasoning:** US1 scopes the admin view to user management "and nothing else" — an admin-creation UI was never asked for, and IaC provisioning is already the accepted pattern for admin lifecycle (FR-AUTH-08). Reset-each-other must be exposed in the UI because it is the stated rationale of FR-AUTH-07 itself; without it, multi-admin support is dead weight. Blocking in-app admin removal prevents the last-admin-removes-themselves lockout, and costs nothing functionally: admins author no planning content (FR-AUTH-05), so the reattribution machinery of FR-AUTH-13 has nothing to do for them anyway.
- **Requirements:** FR-AUTH-18; FR-AUTH-12 already lists all accounts including admins.

### G-44 · A checked item whose quantity grows is silently wrong — **SUPERSEDED by G-77 (2026-08-14)**

> **Superseded.** The gap below is real and its statement still stands; the
> *decision* has been replaced. G-44 resolved it by updating the checked item
> and flagging it; G-77 resolves it by never touching the checked item and
> adding a new unchecked item for the outstanding amount. Kept for the record.

- **Gap:** FR-SHOP-08 correctly preserves check state across re-sync, but consider: a user buys 500 g of rice and checks the item; a new definitive meal raises the requirement to 800 g. The quantity updates on an item the user has already marked as bought — the fact that **more must be bought** is invisible.
- **Decision:** The quantity change is applied, the item stays checked, and the item is visually flagged as updated since it was checked.
- **Reasoning:** The two naive options each destroy information: auto-unchecking erases the user's real-world action (they *did* buy rice — the exact failure G-32 forbids), while silently updating hides the shortfall. Flag-without-uncheck preserves both truths and lets the user decide (uncheck to re-buy the difference, or ignore). This is the same "never silently undo the user's reality" principle already applied in G-04, G-21 and G-32.
- **Requirements:** FR-SHOP-08 (amended).

### G-45 · Mid-week generation would pay for days already past
- **Gap:** Whole-week generation now explicitly targets the current week too (FR-AI-03/-11). Run on a Thursday, it would generate candidates for Monday–Wednesday — slots that can never be cooked — spending capped AI budget (NFR-AI-01) on noise and polluting the week record with meals nobody could have eaten.
- **Decision:** For the current week, generation targets only slots from the current day onward (Europe/Madrid, consistent with FR-MENU-02); past days remain manually editable; weekly ingredient-category counts are honored as far as the remaining slots allow.
- **Reasoning:** Generating un-cookable meals is pure waste under a hard cost cap. Manual editing of past days stays allowed because the archive's value (US25) is as a record of what was actually eaten — users may legitimately backfill reality ("we ordered pizza Tuesday"). Rule counts degrade gracefully rather than erroring, since a half-week arithmetically cannot satisfy full-week quotas and blocking generation entirely would make the feature unusable from Tuesday onward.
- **Requirements:** FR-AI-11 (amended).

### G-46 · Search was added to the library view but not to the flows that pick from it
- **Gap:** G-34 added search/filter to the library *view*, but the too-many-recipes problem it solves exists identically in the three flows that **select** a library recipe: picking a candidate from the library (FR-CAND-02a), choosing an AI reference recipe (FR-AI-02), and pinning a meal in a rule (FR-RULE-04) — the last being a plain dropdown, the worst possible UI for a long list.
- **Decision:** The same search-by-name and cuisine/difficulty filters are available in every library-picking context.
- **Reasoning:** Same problem, same fix; solving it in one surface and not the others just moves the frustration to wherever the user actually needs a recipe. The rule-pinning dropdown is the most urgent case: US26 mandates dropdown-only editing, and an unsearchable dropdown over a growing library degrades into scrolling through hundreds of entries.
- **Requirements:** FR-LIB-04 (amended).
- **Amended by G-68:** what propagates to the three picking flows is now **search by name** only; the filters are gone. The rule-pinning dropdown concern is unchanged.

### G-47 · Library changes were missing from the real-time broadcast list
- **Gap:** FR-RT-01 enumerated candidates, definitive selections, shopping lists and rules — but not the **library**, even though FR-RT-02 declares it fully shared-editable. Two users browsing simultaneously would see stale libraries; worse, one could pick or pin a recipe another user just deleted.
- **Decision:** Library additions, edits and deletions broadcast in real time like everything else.
- **Reasoning:** The omission was an enumeration bug, not a design choice — every argument that justified real-time for rules (shared, editable by anyone, actions depend on current state) applies verbatim to the library. The stale-pick hazard directly feeds G-20's dangling-reference problem, so freshness here protects rule integrity too.
- **Requirements:** FR-RT-01 (amended).

### G-48 · Nothing constrained recipe ingredient units to the shopping list's fixed unit list
- **Gap:** Auto-aggregation matches items only on **name + unit** from a fixed unit list (FR-SHOP-03) — but no requirement constrained the units *inside recipes* to that list. Ingredients written free-form ("un puñado", "2 tazas") or invented by the AI would silently never aggregate, hollowing out US23 for nearly every recipe while appearing to work.
- **Decision:** Every recipe-authoring flow — manual or AI, targeting candidates or the library — expresses ingredient quantities using the same fixed unit list, via dropdown for humans and via prompt instruction plus output validation for the AI.
- **Reasoning:** An aggregation feature is only as good as its inputs; enforcing the vocabulary at authoring time (one dropdown) is trivially cheap, whereas the alternative — fuzzy unit parsing at aggregation time — is exactly the cross-unit-conversion complexity the MVP explicitly rejected (G-39). The AI path needs validation, not just prompting, because model output is not guaranteed to follow instructions; a failed validation is surfaced through the existing per-slot failure flow (FR-AI-12).
- **Requirements:** FR-LIB-05.

### G-49 · Difficulty and cuisine values were unnormalized, breaking the new filters
- **Gap:** FR-LIB-04 filters by cuisine and difficulty, and FR-AI-01 takes difficulty as an AI input — but both fields were free-form. Users writing "fácil", "easy" and "2/5" create three filter buckets for one concept, making the difficulty filter useless as the library grows.
- **Decision:** Difficulty becomes a predefined dropdown scale (e.g. fácil/media/difícil); cuisine stays free text but with suggestions drawn from values already in the library.
- **Reasoning:** Difficulty has a naturally small, closed vocabulary — a dropdown costs nothing and guarantees filterability, consistent with the dropdown-only philosophy the stories already embrace for rules (US26). Cuisine is genuinely open-ended (any cuisine on earth may appear), so closing it would wrongly reject valid values; suggestions-from-existing-values nudges users toward convergence ("Italiana", not "italiana"/"Italian") without forbidding anything.
- **Requirements:** FR-LIB-06.
- **Superseded by G-68:** moot. Cuisine and difficulty no longer exist, so there is nothing left to normalize or constrain to a scale, and FR-LIB-06 is removed. Retained here for the audit trail.

### G-50 · Candidates stored their author but never displayed it
- **Gap:** US15 reads "candidate meals … created by me or other users" — a distinction the user can only make if the author is **shown**. Attribution was stored (it powers FR-SUM-02 and FR-RT-02) but no requirement put it on the candidate itself.
- **Decision:** Each candidate displays its author.
- **Reasoning:** This is the plain reading of the story's wording, and in a collaborative selection flow (US15: pick one candidate to be definitive) knowing *whose proposal* each option is, is part of how a household actually decides. Zero new data — the attribution already exists for other requirements.
- **Requirements:** FR-CAND-04 (amended).

### G-51 · An admin "change password" was arguably permanent
- **Gap:** FR-AUTH-05 lets admins "change/reset" user passwords, but FR-AUTH-11's temporary-password rule named only "creation or reset" — leaving a literal reading where a password *change* produces a permanent password the admin knows, quietly bypassing the mandatory set-password step.
- **Decision:** Any admin-assigned password — creation, change, or reset alike — is temporary and forces the set-password step.
- **Reasoning:** The impersonation argument of G-10 applies identically regardless of which verb the admin used; a distinction between "change" and "reset" that alters the security model would be an accident of wording, not a design.
- **Requirements:** FR-AUTH-11 (amended).

### PEND-14 (raised, not resolved here) · Combined shopping view across the two live weeks
With two live weeks (G-28) there are now two shopping lists, and a user shopping
on Saturday plausibly buys for the rest of the current week *and* the next week
in one trip — merging quantities across both lists by hand. A **combined view**
would serve that, but the stories define the list strictly per week (US21), so
adding one is new product scope, not a completeness fix. Raised as PEND-14 in
`gaps_pending_stakeholders.md` for a business decision. **Resolved 2026-07-04 —
see G-52.**

---

## Part F — Shopping-list scope decision (2026-07-04)

### G-52 · Single button-driven shopping list over both live weeks (resolves PEND-14)
- **Gap:** PEND-14 — with two per-week shopping lists (a consequence of the two live weeks, G-28), a user shopping once for the remainder of the current week plus the next week had to merge quantities across two lists by hand.
- **Decision (stakeholder):** When the user clicks the add-ingredients **button**, the app adds all the ingredients for **definitive-only** meals in the **current week (only days forward from today)** and the **next week**. Consequences worked into the requirements:
  - There is **one shared shopping list**, not two per-week lists — the button's combined scope makes the per-week split meaningless (FR-SHOP-01).
  - The auto-add trigger is an explicit **button press**, superseding the automatic on-definitive-change re-sync chosen in G-21 (FR-SHOP-03, FR-SHOP-06).
  - **Definitive-only** sourcing is reaffirmed (G-04) and now explicit in the story itself (US23 updated).
  - The current week contributes only **today-onward** days (Europe/Madrid), matching the same principle applied to AI generation in G-45 (FR-SHOP-05).
  - Re-sync semantics on each press: quantities updated, new items added, stale **unchecked** auto items removed; manual items, manual overrides (G-21) and **checked** items always preserved (G-32, G-44) (FR-SHOP-06).
  - Archiving adapts: the live list persists across rollovers; a **snapshot** at rollover is stored with the archived week so the historical record (US25) stays complete (FR-ARCH-02 amended).
- **Reasoning:** One list matches how the shopping actually happens — one trip covers the whole horizon — and eliminates by construction the manual cross-list merging PEND-14 identified. The button trigger, though it reverses G-21, is the better fit once the list spans two weeks of in-flux planning: an always-automatic list would churn continuously (quantities bouncing, checked-item flags firing) while users are still proposing and promoting meals, whereas a deliberate press at shopping-prep time produces a stable list exactly when it is needed. The staleness risk that originally justified the automatic trigger is mitigated by the flow itself: the natural moment to press the button is right before shopping, which is also the only moment staleness matters. "Automatically" in the original US23 wording is thus read as "the app computes the ingredients for me," not "without my intent" — confirmed by the stakeholder's own phrasing ("when the user clicks on the button"). Removing stale unchecked items on each press keeps list hygiene, while checked items are never auto-removed because they record a real-world purchase (the G-32 principle).
- **Requirements:** FR-SHOP-01, -03, -05, -06 (amended), FR-ARCH-02 (amended), FR-RT-01 (wording); US23 rewritten in `app_user_stories.md`.
- **Refined (same day):** rollover cleanup of the closed week's bought items — see G-53.

### G-53 · Rollover cleanup of the shared shopping list (stakeholder refinement of G-52)
- **Gap:** G-52 made the shopping list a single, persistent list, but left its rollover behavior unspecified: bought (checked) items would accumulate in the greyed section forever, and nothing guaranteed that items bought *in advance* for the next week would survive the week change.
- **Decision (stakeholder):** When a week is closed, the list clears itself of the already-bought items **from that week**; items from the former next week (now the current week) remain. Interpretation worked into the requirements:
  - Auto items record **which live week(s)** require them — necessary because aggregation (FR-SHOP-03) can merge one item's needs across both weeks.
  - At rollover, **checked** items are removed **unless** they are still required by a definitive meal of the new current week (the former next week). An item needed by both weeks therefore survives, keeping its bought status so nobody re-buys it.
  - **Unchecked** items are untouched by rollover, whatever their week: an unbought item is something a user may still intend to buy, and stale unchecked auto items are already cleaned by the existing button-press re-sync (FR-SHOP-06).
  - Checked **manual** items (which have no meal attribution) are cleared at rollover like other bought items of the finished cycle; unchecked manual items always remain.
  - The archive snapshot (FR-ARCH-02) is taken **before** the cleanup, so the historical record of the closed week shows what was actually bought.
- **Reasoning:** Rollover is the natural end of a purchase's purpose — clearing bought items then keeps the greyed section from growing without bound, with zero user chores. Sparing everything the former next week needs protects exactly the behavior next-week planning exists for (G-28): shopping in advance — wiping those items would mark real purchases as forgotten. Restricting the cleanup to *checked* items follows the established "never silently discard something the user may still act on" principle (G-04, G-21, G-32): only a bought item's job can be finished. Snapshot-before-cleanup preserves record fidelity (US25) at no cost.
- **Requirements:** FR-SHOP-09 (new); FR-MENU-06, FR-ARCH-02 (amended); US24 extended in `app_user_stories.md`.
- **Superseded (2026-08-09) by G-73.** The conditional half of this decision is gone: rollover now clears **every** checked item unconditionally and keeps every unchecked one, so the per-item week attribution in the second bullet is not stored. What survives unchanged is the rest — unchecked items untouched, checked manual items cleared alongside the others, and the archive snapshot taken before the cleanup.

---

## Part G — Second post-integration re-scan (2026-07-04)

A further end-to-end scan after the shopping-list decisions (G-52, G-53)
settled, looking for interactions those decisions created and for systemic
holes surviving all earlier passes. Eight gaps found and resolved; one new
business question raised (PEND-15).

### G-54 · Concurrent shopping-button presses were unprotected
- **Gap:** The button re-sync (G-52) is a compound operation — add, update, and remove many items. Two users pressing it near-simultaneously (a realistic Saturday scenario in a shared household app) could interleave and produce duplicated auto items or conflicting removals. AI generation received exactly this protection (FR-AI-08/-09); the shopping sync never did.
- **Decision:** The re-sync is idempotent and serialized: it deterministically **recomputes** the auto-item set from the in-scope definitive meals, so any number of concurrent presses converge to the same single result.
- **Reasoning:** Recompute-from-source is the natural formulation — the auto-item set is a pure function of the definitive meals in scope, so "apply twice" and "apply once" are identical by construction, which is cheaper and more robust than diff-based patching plus locks. Last-write-wins (G-07) is the right model for *independent field edits*, not for compound derived-state updates, where interleaving corrupts rather than merely overwrites.
- **Requirements:** FR-SHOP-10.

### G-55 · A manual item and an auto item with the same name+unit silently coexist
- **Gap:** A user manually adds "arroz, 500 g"; the button later computes an auto "arroz, 800 g". FR-SHOP-04 rightly forbids the sync from touching manual items — but the result is two rows for one product with no signal, and a shopper buying both quantities.
- **Decision:** Both rows remain (manual data stays inviolate), but the list groups and marks same-normalized-name+unit pairs as likely duplicates for the user to resolve.
- **Reasoning:** Auto-merging was rejected because it would mutate or shadow user-entered data (the household may genuinely want extra rice beyond the menus); silently keeping both was rejected because the duplication is invisible precisely at the moment it costs money (in the store). Surfacing without deciding follows the same-name warning pattern already established for the library (G-26).
- **Requirements:** FR-SHOP-11.

### G-56 · Exact-string name matching quietly fragments aggregation
- **Gap:** Aggregation matches items by name + unit, but "Tomate", "tomate " and "tomáte" are three different strings — so the merge that justifies the whole aggregation feature silently fails for capitalization, stray whitespace, and accents. AI-authored ingredient names (FR-LIB-05 constrains their *units*, not their spelling) make collisions routine. The same weakness affects the cuisine filter and suggestions (G-49).
- **Decision:** Name matching for aggregation — and cuisine matching for filters/suggestions — is case-, accent- and leading/trailing-whitespace-insensitive. No further fuzzy matching (singular/plural, synonyms) in the MVP.
- **Reasoning:** Case/accent/trim normalization is deterministic, cheap, and captures the overwhelming majority of accidental mismatches in Spanish text ("Jamón"/"jamon"). Singular/plural stemming and synonym matching ("tomate cherry" vs "tomatitos") are genuinely hard, error-prone, and were already implicitly rejected with cross-unit conversion (G-39) — the fixed-vocabulary philosophy stops at what can be normalized losslessly.
- **Requirements:** FR-SHOP-03 (amended), FR-LIB-06 (amended).
- **Amended by G-68:** the cuisine half of this rule is removed with the attribute. Case-/accent-/whitespace-insensitive matching still governs **ingredient names** for shopping aggregation (FR-SHOP-03), which was always the load-bearing case.

### G-57 · Two live weeks created a mis-targeting hazard the UI never addressed
- **Gap:** Since G-28 every planning action has a target week, but no requirement made the active week visible — a user believing they're filling next week could add candidates, promote definitives, or launch a 14-slot AI generation into the wrong week. The generation confirmation prompt (FR-AI-05) showed the rules but not **which week** it was about to fill.
- **Decision:** Every week view, summary, and week-scoped action is labelled with the week (current/next) and its Monday–Sunday date range; the generation confirmation prompt displays the target week the same way.
- **Reasoning:** Mis-targeting is the characteristic new failure mode of the two-week model: cheap to prevent (a persistent label), expensive to suffer (an AI run costs capped budget, FR-AI-08's idempotency will even *prevent* the "same" run from being re-issued at the correct week if rules match, and cleanup means deleting 14 candidates by hand). Dates rather than bare "current/next" labels because around midnight Sunday the words change meaning while the dates do not (G-02).
- **Requirements:** FR-UX-06 (new), FR-AI-05 (amended).

### G-58 · The "unknown user" placeholder name could be claimed by a real account
- **Gap:** G-29's placeholder is rendered wherever a removed author's name would appear — but nothing stopped an admin from creating a real user named "unknown user" (or its Spanish rendering), making genuine attributions indistinguishable from removed-account placeholders.
- **Decision:** The placeholder name is reserved (rejected by username validation), and the placeholder renders as a distinct system label rather than as a regular account name.
- **Reasoning:** The placeholder's entire value is unambiguity (that was the argument in G-29); a colliding real username destroys it retroactively across the archive. Distinct rendering (e.g. italicized system style) additionally protects against *visual* spoofing without depending on string comparison alone.
- **Requirements:** FR-AUTH-17 (amended).

### G-59 · Nothing warned about duplicate candidates in a slot
- **Gap:** Several users independently proposing the same recipe for the same slot (typically picked from the same library entry) creates identical candidates side by side — noise in exactly the view where US15 asks users to make a choice.
- **Decision:** Adding a candidate whose name matches an existing candidate in that slot triggers a duplicate warning; adding remains possible.
- **Reasoning:** Warn-don't-block is the established pattern (G-26 for the library, G-55 for the shopping list): near-duplicates are sometimes intentional (same dish, different tweaks — snapshots make them genuinely distinct, G-05), so the system surfaces the collision and lets the human decide. Blocking would also race with real-time concurrent adds (G-07), whereas a warning degrades gracefully.
- **Requirements:** FR-CAND-01 (amended).

### G-60 · The breached-password blocklist was implicitly English-centric
- **Gap:** FR-AUTH-15 requires a common/breached-password blocklist, but standard lists are dominated by English passwords. This app's users are Spanish speakers (US20): the guessing wordlist an attacker would actually use — "contraseña", "hola1234", Spanish names and football clubs — is precisely what a default list misses.
- **Decision:** The blocklist must include common Spanish-language passwords in addition to the standard corpus.
- **Reasoning:** A blocklist is a model of the attacker's dictionary; NIST 800-63B's own rationale (G-30) says to block what attackers try first. For a Spanish user base that means Spanish passwords — an English-only list satisfies the letter of FR-AUTH-15 while missing its point. (Also fixed in passing: a typo in FR-AUTH-15, "unruncated" → "untruncated".)
- **Requirements:** FR-AUTH-15 (amended).

### G-61 · Week rollover accreted into a multi-step transaction with no failure semantics
- **Gap:** Rollover now performs five steps in order: archive the ending week (G-02), snapshot the shopping list (G-52), promote next→current (G-28), initialize the new next week, and clean bought items (G-53). A crash between steps — routine in scheduled cloud jobs — leaves half-rolled state (e.g. week archived but list never cleaned, or double cleanup on retry), and no requirement said the job must tolerate this.
- **Decision:** Rollover is an atomic, idempotent, re-runnable job: retrying after partial failure completes the remaining steps without data loss, double-archiving, or double-cleanup.
- **Reasoning:** Each individual step was specified in a different gap resolution; their composition into one fragile sequence happened by accretion, which is exactly when transactional requirements get forgotten. Idempotent re-runnability is the same discipline already imposed on AI generation (FR-AI-08) and the shopping sync (G-54), applied to the one scheduled job whose failure would corrupt the archive (US25) — the app's only unrecoverable data.
- **Requirements:** FR-MENU-08.

### PEND-15 (raised, not resolved here) · Accessibility target
No pass so far has addressed accessibility (keyboard navigation, screen-reader
labels, color contrast — relevant to the greyed-out checked items of G-32).
Like the browser matrix (PEND-11), this is QA/compliance scope the stories are
silent on, so it needs a business decision rather than an invented requirement:
none / basic good practices / formal WCAG 2.1 AA. Raised as PEND-15 in
`gaps_pending_stakeholders.md`. **Resolved same day — see G-62.**

---

## Part H — Final exhaustive sweep (2026-07-04)

Method note: earlier re-scans had settled into a cadence (a handful of
auto-resolvable gaps plus one stakeholder question per pass), which the
stakeholder flagged as an artifact of scoping, not of the spec. This sweep
therefore ran with no target count: every requirement section was re-read
against every story and against the data model, and the pass explicitly
recorded its **negative space** — items examined and rejected — so the result
is auditable. Outcome: one PEND closure (G-62), **two semantic gaps** in core
features (G-63, G-64), three smaller completeness fixes (G-65 to G-67), and
**zero new stakeholder questions**.

### G-62 · Accessibility: browser defaults only (closes PEND-15)
- **Gap:** PEND-15 asked what accessibility level the MVP should target.
- **Decision (stakeholder):** No accessibility requirements beyond browser defaults — this is an MVP targeting basic core functionality.
- **Reasoning:** Recorded as an explicit **scope-exclusion requirement** (rather than silence) so developers and QA don't re-open the question or gold-plate: the absence of accessibility work is a decision, not an omission.
- **Requirements:** FR-UX-07 (new, scope exclusion).

### G-63 · Nothing defined how a meal gets an ingredient category
- **Gap:** The general rules count "meals per week per ingredient category" (US26) — the core lever of the whole rules feature — yet recipes store no category (FR-LIB-03), and no requirement said how a recipe is determined to be "meat" or "legumes". The enforcement mechanism of FR-RULE-04's most important rule type was literally undefined: un-implementable as written, unverifiable after generation.
- **Decision:** Two-tier enforcement, stated explicitly. Deterministic rules (pinned meals, disabled days) are enforced by the **system** (FR-AI-11, unchanged). Ingredient-category counts are conveyed to the **AI as explicit prompt instructions** and honored **best-effort** based on each recipe's ingredients; the MVP stores no per-recipe category and performs no post-generation verification. The category list itself is a fixed, predefined configuration set — the same pattern as the unit list (G-39).
- **Reasoning:** The deterministic alternative — a category attribute on every recipe, set at authoring and inferred for AI output — would burden every authoring flow with a classification chore, still be wrong at the edges (is paella "fish" or "carbohydrates"?), and enable a verification step nobody asked for. Since **all** whole-week generation flows through the AI (even library-only mode is the AI selecting from the library, FR-AI-03), the AI reads actual ingredients anyway and is better positioned to categorize than a single stored enum. Best-effort is honest about what an LLM guarantees, consistent with the qualitative treatment of "healthy/balanced" the stakeholder confirmed in G-36. Fixed category list via config follows the established fixed-vocabulary philosophy (units G-39, difficulty G-49).
- **Requirements:** FR-AI-04, FR-RULE-04 (amended).

### G-64 · AI recipes had no servings assumption, making quantities arbitrary
- **Gap:** Recipe ingredient quantities feed the shopping list (US23), but nothing told the AI how many people it was cooking for. Each generated recipe would silently assume its own household size, so aggregated quantities — the shopping list's entire output — would mix incompatible baselines. Manually-written recipes don't have this problem (the household writes for itself), which is exactly why the gap was invisible until AI generation was considered end-to-end.
- **Decision:** Every AI generation prompt (single-recipe and per-slot whole-week) states a **configured number of servings** (deployment configuration, e.g. 4 diners).
- **Reasoning:** A deployment config is the MVP-minimal fix: no new UI, no new rule type, one constant matching the fixed household this app serves (~2–10 users, G-35). Promoting it to a user-editable rule later is a trivial upgrade if wanted, but inventing that UI now would be scope the stories don't ask for. Leaving it unspecified was not an option — an unstated assumption in a prompt isn't a default, it's nondeterminism.
- **Requirements:** FR-AI-13 (new).

### G-65 · A re-seeded bootstrap admin credential was arguably permanent
- **Gap:** FR-AUTH-08 recovers a locked-out admin by re-seeding the bootstrap credential from the IaC-managed secret — but unlike every other admin-assigned password (G-10, G-51), nothing said the re-seeded credential was temporary. A literal reading left a long-lived password sitting in Secrets Manager that also grants full application access.
- **Decision:** A re-seeded credential behaves like any admin-assigned password: valid only to reach the mandatory set-password step.
- **Reasoning:** Closes the last remaining path by which a password known outside the account holder's head could operate the app — the same argument as G-10/G-51, applied to the operational plane. The IaC secret remains useful for its actual purpose (recovery bootstrap); after the forced set-password it simply no longer matches the live credential, which is fine and even desirable.
- **Requirements:** FR-AUTH-08 (amended).

### G-66 · Library-only generation against an insufficient library failed undefined
- **Gap:** Whole-week generation in library-only or mix mode (FR-AI-03) assumes the library holds enough suitable recipes. A young library (day one, or after aggressive pruning — US18 lets anyone delete) may not cover 14 slots under the active rules; behavior in that case was unspecified, risking a silent half-filled week that looks like a bug.
- **Decision:** Surfaced through the existing per-slot failure mechanism with a clear message naming the cause (insufficient library recipes), never a silent partial result.
- **Reasoning:** Reuses machinery rather than adding any: FR-AI-12 already defines per-slot failure surfacing, and per-slot independence (FR-AI-09) means the week fills as far as the library allows, with honest gaps. The user's remedies are all existing features (add recipes, switch to mix/AI-only mode, relax rules), so all the system owes them is an accurate explanation.
- **Requirements:** FR-AI-12 (amended).

### G-67 · Whether a definitive meal stays editable was ambiguous
- **Gap:** FR-CAND-01 makes candidates editable and FR-SUM-01 makes the summary read-only; a promoted (definitive) meal is both a candidate and the summary's content. One reading allows editing it from the menu view, another treats promotion as freezing content — a question a developer hits in week one, with the archive's fidelity (US25) at stake either way.
- **Decision:** A definitive meal remains editable like any candidate; edits propagate everywhere it is displayed. "Read-only" in FR-SUM-01 restricts the **summary view's capabilities**, not the meal's content, which only freezes at archival (FR-ARCH-02).
- **Reasoning:** Households adjust ("add more rice, my parents are coming") right up until cooking; forcing a clear-reselect-repromote dance (FR-CAND-08 + FR-CAND-05) to fix a typo would punish the normal case. The collaborative safety net for content edits is the same as everywhere else: attribution, real-time broadcast, and confirmations (G-07, G-24). The record only needs to be immutable once the week is history, which FR-ARCH-02 already guarantees.
- **Requirements:** FR-CAND-05 (amended).

### G-68 · Cuisine and difficulty were scope the household never asked for
- **Gap:** Recipes carried two classification attributes — **cuisine** and **difficulty** — introduced as AI-generation inputs (FR-AI-01) and then reused as library filters (G-34, G-46). Each one dragged a tail behind it: a closed difficulty vocabulary to agree on (G-49), accent-insensitive cuisine normalization (G-56), two extra fields in every authoring flow, and a pending architecture decision on the scale's literal values. No user story asks to plan meals *by* cuisine or difficulty; they entered as prompt-flavoring metadata and were promoted to first-class data by the filter requirement, not by a stated need.
- **Decision:** Both attributes are **removed from the product**. Recipes no longer store cuisine or difficulty; AI single-recipe generation takes ingredients and tools only; library discovery is **search by name** alone. FR-LIB-06 is removed outright. A per-recipe **kcal/calorie** attribute was never in scope and remains out (G-36).
- **Reasoning:** For a household of 2–10 people the library is small enough that name search carries it, and the two fields cost more than they returned: they were the *sole* justification for the difficulty scale decision (G-49), for half of the text-normalization rule (G-56), and for a pending architecture decision (`docs/architecture.md` §2). Removing them retires all three at once and shortens both authoring flows. The accepted cost is discovery UX at scale — once the library passes roughly 80 recipes, name search alone gets thin, and the remedy then is a proper tag/search facet driven by an actual story rather than two fields inherited from a prompt form.
- **Requirements:** FR-LIB-06 (removed); FR-CAND-03, FR-LIB-03, FR-LIB-04, FR-AI-01 (amended). Supersedes G-49; amends G-34, G-46, G-56.

### Examined and rejected in this sweep (recorded for auditability)
- **Offline support for in-store shopping** — real value, but a service-worker/sync architecture is far beyond "basic core functionality"; stores have connectivity and the list is a lightweight page.
- **GDPR/data-protection formalities** — a private household app storing only usernames; user removal (G-29) already provides practical erasure. Compliance paperwork is not MVP scope.
- **Per-recipe ingredient-category attribute** — rejected within G-63 (authoring burden, edge-case wrongness, enables verification nobody asked for).
- **Household-size as a user-editable rule** — rejected within G-64 (config constant suffices; UI promotion is a later trivial upgrade).
- **Presence indicators / "who's online"** — not in any story; real-time change broadcast (US19) already conveys activity.
- **Shopping-list export/print/share** — not in any story; the responsive mobile site (US6) is the in-store experience.
- **AI content-safety guardrails beyond the non-medical label** — recipe generation with fixed input dimensions is a low-risk domain; the non-medical labelling (FR-AI-06) covers the realistic concern.
- **Field-level validation minutiae** (name lengths, quantity bounds, item ordering within shopping sections) — implementation details below requirement granularity; es-ES validation messaging is already required (FR-UX-03).
- **Session-keepalive semantics of the real-time connection** (does an open WebSocket count as activity for FR-AUTH-16?) — implementation detail with no user-visible ambiguity worth legislating.

---

## Part I — Access-pattern review reversals (2026-08-03)

While drafting the access-pattern catalogue (`lab-final-patrones-acceso.xlsx`),
two requirements were found to be wrong **as authored**, not merely ambiguous.
Both were reversed by direct decision of the requirements owner, who authored
the originals. Recorded here because each **supersedes an earlier resolution**
that argued the opposite case — the reasoning below is what changed, not the
process.

### G-69 · Recipes need a stored ingredient category after all (supersedes G-63)
- **Gap:** G-63 decided the MVP would store **no** per-recipe ingredient category, leaving FR-RULE-04's category counts to be honored best-effort by the AI from raw ingredients. That made the library's only discovery mechanism name search (G-68), and made post-generation verification of the rules impossible by construction. Once the access patterns were written down, the consequence became concrete: the library-read pattern ("Obtener biblioteca") was drafted with a `tipoAlimento` filter parameter that no stored attribute could satisfy.
- **Decision:** Every recipe stores exactly **one** ingredient category (`tipoAlimento`) — the one that **predominates** in the dish — drawn from the same fixed set FR-RULE-04 already defines for the rules. It is captured in every authoring flow via dropdown; AI output is instructed and validated against the same set. The library gains a **filter by category** alongside name search. Category counts become verifiable after generation instead of best-effort only.
- **Reasoning:** G-63 rejected the attribute on three grounds, and two of them have weakened. (1) *Authoring burden*: a single dropdown, in flows that already carry a dropdown for units (FR-LIB-05) — marginal. (2) *Wrongness at the edges*: real, and explicitly accepted — "lentejas con chorizo" is filed under whichever category prevails, so the counts approximate composition and are **not** a nutritional measure. FR-AI-04 now says so out loud rather than leaving readers to assume precision. (3) *Enables verification nobody asked for*: the owner is now asking for it. The compensating gain G-63 could not have priced is that the household regains a discovery axis the library lost entirely in G-68, at the cost of one enum instead of the two free-form attributes that removal retired.
- **Requirements:** FR-LIB-03, FR-LIB-04, FR-AI-04, FR-RULE-04 (amended). **Supersedes G-63**; reverses the "per-recipe ingredient-category attribute" rejection recorded in the Part H negative space.

### G-70 · The AI cost cap is global, not per-user (supersedes G-38)
- **Gap:** G-38 enforced the €50/month AI budget through a **per-user daily generation cap**. That obliged the application to store and atomically increment a per-user-per-day counter — a persistence access pattern, a concurrency problem, and a figure to derive from provider pricing (listed as open work in `architecture.md` §2.1) — all to ration a resource among 2–10 trusted members of one household.
- **Decision:** The cap is enforced **globally for the deployment** through AWS cost-control tooling. The application stores **no** per-user quota and performs no counting. It surfaces a friendly es-ES message when generation is unavailable because the cap is reached.
- **Reasoning:** Per-user fairness is a mechanism for defending a shared budget against untrusted or adversarial consumers. This household is neither: the members share a kitchen, and the failure mode the cap actually guards against is a runaway loop or a pricing surprise, which a global ceiling catches and a per-user quota does not catch any sooner. Removing it deletes a counter, an atomicity requirement, and a pending numeric decision. **The accepted cost is stated deliberately:** one enthusiastic user can exhaust the month's budget for everyone, with no in-app remedy. **The known hazard is also stated:** AWS Budgets *alert*; they do not *stop* spend. A budget alarm alone satisfies the letter of this requirement while still permitting an unbounded bill, so NFR-AI-01 now requires an actual enforcing path (Budget action or equivalent), not merely notification.
- **Requirements:** NFR-AI-01, FR-AI-10 (amended). **Supersedes G-38.** FR-AI-10 still said regenerations "count toward the generation caps", a dangling reference to the per-user counter this decision removes; it now states that each regeneration is a fresh invocation consuming the global budget. Obsoletes the "per-user daily generation cap" references in `docs/architecture.md` (the P4 row in §2 and the §2.1 item) and the PEND-03 answer in `docs/gaps_pending_stakeholders.md` — both files were left untouched, the first because it is human-owned, the second because it is a frozen record of what the stakeholder was actually asked. See the desync register in `docs/access_patterns_review.md` §8.

### G-71 · Whole-week generation ignored the week it was generating into
- **Gap:** FR-AI-11 defined generation's targeting from the **rules and the clock** only — disabled days, pinned slots, days already past. Nothing consulted the **current contents** of the week, which left two behaviours undefined. (1) A slot already holding a **definitive** meal was still a target, so generation would pile candidates underneath a decision the household had already made. (2) The weekly ingredient-category counts of FR-RULE-04 did not say whether they described the week's **final state** or merely the **generated output** — so with a "3 fish meals" rule and two fish meals already planned, an implementer could defensibly add one or add three. The clause "as far as the remaining slots allow" implied the former; the requirement never said it.
- **Decision:** Both resolved toward the week's actual state. Slots holding a definitive are **skipped entirely**, and an existing definitive **outranks a pin rule** — the skipped pin is reported through the existing per-slot messaging (FR-AI-12) rather than applied silently. Category counts describe the **week's final state**: existing meals count toward each total and generation supplies only the remainder.
- **Reasoning:** Both fall straight out of invariant #2 — *never silently undo the user's reality*. A definitive meal is the strongest signal of intent in the product (FR-CAND-05); burying it under generated candidates, or overwriting it because a rule was written weeks earlier, inverts the priority between a standing preference and a present decision. Reporting the skipped pin rather than swallowing it follows the same "flag it, keep both, let the human resolve" clause. On the counts, final-state semantics is the only reading under which the rules mean what a household thinks they mean; the alternative makes the totals a property of one button press rather than of the week, and lets repeated presses compound past any limit. The cost is that generation must now **read the week** before targeting — a projection of name, category and definitive-status per slot, the same shape the week grid and the library index already need.
- **Requirements:** FR-AI-11 (amended). Depends on the per-recipe category introduced by G-69 — final-state counting is only computable because meals now carry `tipoAlimento`. FR-RULE-07 is unchanged: rule-set satisfiability is still validated against the **rules** at edit time; a runtime shortfall caused by occupied slots remains an FR-AI-12 per-slot message.

---

## Part J — Shopping-list MVP simplification (2026-08-09)

Continuing the access-pattern review, the shopping-list requirements were
re-examined against the attributes an item would actually have to carry. The
requirements owner judged the accumulated behaviour to be **over-specified for
the MVP** and cut it back. All three entries below are owner decisions
overriding the freeze in `CLAUDE.md`, in the same manner as Part I, and each
**supersedes an earlier resolution** that argued for the machinery now removed.

The three cuts are one idea seen from three sides: **the shopping list stores
no provenance.** An item is a name, a quantity, a unit and a checkbox. Every
behaviour that required knowing *where an item came from* — override
protection, stale-item removal, week attribution, duplicate marking — is gone
with it.

### G-72 · Re-sync is additive, which deletes the whole provenance model (supersedes G-21)
- **Gap:** FR-SHOP-06 made the button a read-reconcile-write: update quantities, add new items, and **remove** stale unchecked auto items while preserving manual items, manual overrides and checked items. Removal is the expensive half. To delete safely it must distinguish auto from manual (FR-SHOP-04) and must further distinguish an auto item a user had edited — a **third** state, since neither boolean covers it (G-21). That is a provenance attribute on every row, an override transition on every edit, and a destructive branch that must be right every time, all so the list can tidy itself.
- **Decision:** Re-sync is **purely additive**. It adds ingredients not yet present and updates the quantity of ones already present under the same normalized name + unit. **It never removes anything.** The MVP stores no auto/manual marker and no manual-override state. A user edit to a quantity re-sync also derives may be overwritten by a later press; a no-longer-needed item stays on the list until someone deletes it (FR-SHOP-02) or buys it and rollover clears it (FR-SHOP-09).
- **Reasoning:** The destructive branch was carrying the entire data model. Removing it makes FR-SHOP-04's guarantee — re-sync must not delete manual items — true *by construction* rather than by an attribute that has to be maintained correctly across three flows. It also makes FR-SHOP-10's idempotence nearly free: an additive merge keyed on normalized name + unit is convergent by definition, so concurrent presses cannot duplicate or race on removals. **The accepted costs are stated deliberately.** (1) The list accumulates: uncheck-and-forget items and ingredients from meals later un-promoted linger until removed by hand. In a household list that a human reads weekly, that is a chore, not a defect. (2) A deliberate manual edit ("we already have rice, buy 1 not 3") can be silently reverted by the next press — the exact failure G-21 was written to prevent. The judgement is that a household of 2–10 people re-editing one row occasionally is cheaper than a three-state provenance model, and that FR-SHOP-02's manual delete is the remedy when it matters.
- **Requirements:** FR-SHOP-04, FR-SHOP-06, FR-SHOP-10 (amended). **Supersedes G-21**'s preserve-on-edit principle for the shopping list specifically; the same principle stands untouched everywhere else it applies (G-04, G-32, ~~G-44~~ → **G-77**, which supersedes G-44 and applies the principle more strictly still: a checked item is not merely preserved, it is never written to at all).

### G-73 · Rollover clears bought items unconditionally (supersedes G-53)
- **Gap:** FR-SHOP-09 cleared checked items *except* those still required by a definitive meal of the new current week. That exception is the sole reason the requirement went on to demand that auto items **record which live week(s) require them** — a stored attribute existing entirely to answer one question, once a week, in a job that already reads the new current week anyway.
- **Decision:** At rollover the list is cleared of **every checked item**, with no requirement test. **All unchecked items remain**: an unchecked item is shopping still pending, and pending shopping does not expire because the calendar turned over. The per-item week attribution that the old FR-SHOP-09 required — "auto items shall record **which live week(s)** require them" — is therefore not stored at all. No attribute name was ever assigned to it; it is simply gone.
- **Reasoning:** The check state already carries the meaning the week attribution was reconstructing. Checked means bought; a bought item has served its purpose and the household will re-add it via the button if the new week needs it again — which is exactly what the button is for, and FR-SHOP-06's additive merge now makes that safe. Unchecked means not yet bought, and that is true regardless of which week motivated it. The discarded case is an item bought in advance for the incoming week and then cleared, forcing one button press to restore it; against that, the model loses an attribute, the rollover job loses a read-and-compare step, and FR-MENU-08's idempotence gets easier, because "delete all checked" is naturally re-runnable while a conditional delete is not.
- **Requirements:** FR-SHOP-09, FR-MENU-06 (amended). **Supersedes G-53.** FR-MENU-08 is unchanged and gets simpler to satisfy.

### G-74 · Duplicate grouping was machinery for a case that no longer arises (supersedes G-55)
- **Gap:** FR-SHOP-11 required an auto item and a manual item sharing a normalized name + unit to both remain, but be **grouped and visually marked as likely duplicates**. It was written when re-sync appended alongside manual items rather than merging with them, and it depends on the auto/manual distinction G-72 has now removed.
- **Decision:** FR-SHOP-11 is **removed from the product**. Re-sync merges on normalized name + unit (FR-SHOP-06), so an exact match produces one row, not two. Entries differing only by a form the normalization deliberately declines to fold — "tomate" versus "tomates", per the singular/plural exclusion in FR-SHOP-03 and G-56 — simply sit next to each other with no special treatment.
- **Reasoning:** With merge-on-match there is no duplicate to group in the case the requirement actually named. What survives is near-duplicates that differ textually, and the honest position is that the MVP does not detect those: FR-SHOP-03 already refused stemming and synonym matching as error-prone (G-56), so a "likely duplicate" marker would have to be driven by the same matching that requirement rejected, or by provenance that G-72 has deleted. A user seeing two similar lines edits or removes one with FR-SHOP-02, which is the same remedy the requirement prescribed, minus the UI that pointed at them.
- **Requirements:** FR-SHOP-11 (removed). **Supersedes G-55.** Follows the FR-LIB-06 precedent of G-68: the requirement row is kept, struck through, and annotated rather than deleted, so the id never silently disappears.
- **Reasoning corrected 2026-08-14 by G-77 — the outcome stands, the argument does not.** The claim above that "re-sync merges on normalized name + unit, so an exact match produces one row, not two" is **no longer true**: under G-77 a checked item and an unchecked item deliberately share a normalized name + unit, because the outstanding amount is carried by a new row rather than by modifying a purchase. FR-SHOP-11 stays removed, on a narrower argument: the two rows are **not duplicates**, they are a purchase and a remainder, and they read correctly precisely because the check state already separates them into two sections on screen (FR-SHOP-08). Grouping them would obscure the distinction the user needs. What G-74 originally denied — a *grouping and marking* UI for likely duplicates — is still not wanted, and the near-duplicate case it also covered ("tomate"/"tomates") is unaffected.

---

## Part K — Compliance-pass corrections (2026-08-13)

Raised by the access-pattern compliance pass of AP1–AP23 against this
specification (`docs/access_patterns_review.md` §9). The entry below is an owner
decision overriding the freeze in `CLAUDE.md`, in the same manner as Parts I and
J, and was directed explicitly.

### G-75 · FR-AUTH-13 still claimed shopping-list items are authored content
- **Gap:** FR-AUTH-13 requires content authored by a removed account to be retained and reattributed to the "unknown user" placeholder, and enumerates that content as "candidate meals, library recipes, definitive-meal promotions, rule edits, **shopping-list items**". Since G-72 a shopping-list item is a name, a quantity, a unit and a checkbox — it stores **no author**. The clause names an attribution that does not exist, so it is not merely unimplemented but unimplementable, and a reviewer checking FR-AUTH-13 against the access-pattern catalogue would correctly report the catalogue as non-compliant against a requirement that cannot be met by any catalogue.
- **Decision:** Remove **shopping-list items** from the FR-AUTH-13 enumeration. The remaining four categories are unaffected and keep the render-time resolution of G-29. The struck-through phrase is kept inline with an annotation, following the FR-LIB-06 / FR-SHOP-11 precedent, so the cut stays visible rather than silently disappearing.
- **Reasoning:** This is a leftover, not a change of intent. Part J removed provenance from the shopping list without revisiting the requirements that referenced it from elsewhere — the same class of desync that `docs/access_patterns_review.md` §8 was created to track, found this time in a frozen document rather than a derived artifact. No behaviour changes: nothing today writes an author onto a shopping item, so nothing stops doing so. What changes is that the specification stops asking for something the data model deliberately does not carry.
- **Requirements:** FR-AUTH-13 (amended). Consistent with G-72; no supersession — G-29 stands, with a shorter list.

---

## Part L — Rule attribution removed from the MVP (2026-08-13)

Directed by the requirements owner during the access-pattern compliance pass,
overriding the freeze in `CLAUDE.md` in the same manner as Parts I, J and K.

### G-76 · Rule edits are not attributed in the MVP
- **Gap:** FR-RULE-06 required every shared-rule edit to be **attributed**, and FR-SUM-03 named "rule edits (FR-RULE-06)" among the attributions that must fall back to the "unknown user" placeholder; FR-AUTH-13 likewise listed "rule edits" among the content a removed account leaves behind. The access-pattern catalogue carries no author on either rules pattern, so the compliance pass reported the catalogue non-compliant against three requirements at once.
- **Decision:** **Rule attribution is out of MVP scope.** A rule stores no author. FR-RULE-06 keeps "any user may edit" and the real-time broadcast, and drops the attribution clause. FR-SUM-03 drops rule edits from its enumeration. FR-AUTH-13 drops "rule edits" from the content it reattributes. Struck-through inline with an annotation, following the FR-LIB-06 / FR-SHOP-11 / G-75 precedent.
- **Reasoning:** Attribution earns its place where the product actually shows it. A candidate meal displays its author (FR-CAND-04) and the summary shows who promoted a meal (FR-SUM-02) — both are on screen, both change how the household reads the plan. Rules are a dozen dropdown-selected rows in a shared settings screen that anyone may edit by design (G-37, no owner/governance role); nothing in the product surfaces who last touched one. Carrying an author on every rule write, plus the removed-user resolution path behind it, buys a field no view renders. Same judgement as Part J's provenance cut, applied to a different collection.
- **Requirements:** FR-RULE-06, FR-SUM-03, FR-AUTH-13 (all amended). Does not supersede G-37 or G-29, which stand with narrower scope.
- **Flagged, not changed — outside the instruction given:** **FR-RT-02** still reads "any user may view and edit candidates, the library, and **the shared rules**. Concurrent edits resolve last-write-wins **with author attribution**." Its last-write-wins clause is unaffected, but the attribution half no longer holds for the rules third of that sentence. Left for an explicit decision rather than extended silently. Derived artifacts (`docs/coverage_analysis.md`, `docs/app_user_stories.md` US26) not yet re-synced for G-76.

---

## Part M — The remainder is a new item, not an edit to a purchase (2026-08-14)

Directed by the requirements owner during the access-pattern compliance pass,
overriding the freeze in `CLAUDE.md` in the same manner as Parts I, J, K and L.

### G-77 · A checked item is never written to; the shortfall becomes its own item (supersedes G-44)
- **Gap:** G-44 handled the case where a user buys 500 g of rice, checks it, and a newly promoted meal raises the week's requirement to 800 g. Its decision was to update the checked item to 800 g, keep it checked, and **visually flag it as updated since it was checked**. That flag is not renderable from the data the MVP stores: "updated since checked" compares the quantity **at check time** against the quantity **now**, and the item carries only the latter — the re-sync write overwrote the former. Delivering G-44 therefore required a new stored attribute on every shopping item, which is the provenance Part J had just finished removing.
- **Decision:** **Re-sync never modifies a checked item at all** — not its state, not its quantity. Per normalized name + unit it computes the **outstanding** amount (required by the in-scope definitive meals, minus whatever checked items already carry) and writes that to the matching **unchecked** item, creating one if none exists. When the outstanding amount is zero or less, nothing is added. In the rice case the checked `arroz 500 g` is left alone and a new unchecked `arroz 300 g` appears — the amount still to buy, not the gross requirement. A checked item and an unchecked item may therefore share a normalized name + unit; the surrogate `idIngrediente` already permits this.
- **Reasoning:** The shortfall is not a property of the purchase, so it does not belong on the purchase's row. It is a new thing to buy, and the list already has a perfectly good way to express a new thing to buy — a new unchecked item, which surfaces in the section the user actually shops from. This is the "never silently undo the user's reality" principle (G-04, G-32) taken further than G-44 took it: G-44 still wrote to the row recording a real-world purchase and then papered over the write with a flag; G-77 does not write to it. **It also costs the data model nothing** — no new attribute, no conditional write, and no access pattern: re-sync already reads checked quantities through "Obtener lista de la compra", and the per-item write already creates rows. The alternative designs considered — a stored `isActualizadoDesdeCompra` boolean, or storing the quantity at check time and deriving the flag — were both rejected as machinery for a flag the product does not need. **The quantity written is the remainder, not the gross requirement**, because a user shown `arroz 800 g` after buying 500 g would buy 800 more.
- **Requirements:** FR-SHOP-06, FR-SHOP-08, FR-SHOP-10 (amended). **Supersedes G-44.** FR-SHOP-03 is unchanged: it defines the required set computed from meals, not how that set is applied to the list.
- **Corrects G-74's reasoning without reopening it:** FR-SHOP-11 stays removed, but G-74's argument — "an exact match produces one row, not two" — is now false. The replacement argument is recorded on G-74 itself: the two rows are a purchase and a remainder, not duplicates, and FR-SHOP-08's two-section display already separates them.
- **Left unresolved, deliberately:** FR-SHOP-10 keeps the word **serialized**. Two concurrent presses can still both compute the same outstanding amount and both create a row. That is a concurrency-control question for the data-structure pass, not for the access-pattern catalogue, and the owner parked it explicitly.

---

## Part N — Completing the rule-attribution cut (2026-08-14)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I, J, K, L and M.

### G-78 · FR-RT-02 still attributed rule edits (completes G-76)
- **Gap:** G-76 removed rule authorship from FR-RULE-06, FR-SUM-03 and FR-AUTH-13, and Part L flagged that **FR-RT-02** was left asserting the same thing: "any user may view and edit candidates, the library, and **the shared rules**. Concurrent edits resolve last-write-wins **with author attribution**." One sentence covering three collections, of which only two still have authors.
- **Decision:** FR-RT-02's last-write-wins clause is unchanged for all three collections. **Author attribution is scoped to candidates and library recipes only**; a rule edit is last-write-wins with no author recorded.
- **Reasoning:** Completes G-76 rather than adding to it. Last-write-wins and attribution are independent concerns — the first is a conflict-resolution policy that needs no author, the second is a display concern that does. The original sentence bundled them, which is why removing rule authorship left the requirement half-true.
- **Requirements:** FR-RT-02 (amended). Completes G-76; supersedes nothing.

---

## Part O — Promotion attribution removed from the MVP (2026-08-14)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I through N.

### G-79 · Who promoted a meal is not recorded
- **Gap:** FR-SUM-02 required the weekly summary to display **who made each meal definitive**. That is a second, distinct attribution: FR-CAND-04 already requires each candidate to display **its author**, and the two are routinely different people — one household member proposes a dish, another promotes it. The access-pattern catalogue carries exactly one attribution per meal, `añadidoPor`, so the compliance pass reported FR-SUM-02 as unsatisfiable without a second attribute plus its own removed-user resolution path (FR-SUM-03).
- **Decision:** **Promotion attribution is out of MVP scope.** FR-SUM-02 is removed. The meal's existing author (`añadidoPor`, FR-CAND-04) is what the summary displays; nothing records who promoted it. FR-SUM-03 drops the promotion clause, and FR-AUTH-13 drops "definitive-meal promotions" from the content it reattributes, leaving candidate meals and library recipes.
- **Reasoning:** Same judgement as G-76 applied to a different collection: an attribute is worth carrying when a view depends on it and the household reads it. "Who proposed this dish" is the interesting question and it is already answered. "Who clicked promote" is a second field, a second write path, and a second removed-user fallback, to distinguish an action that in a 2–10 person household is usually visible in conversation and rarely disputed. The requirement row is kept, struck through and annotated, following the FR-LIB-06 / FR-SHOP-11 precedent.
- **Requirements:** FR-SUM-02 (removed), FR-SUM-03, FR-AUTH-13 (amended). Narrows G-29 without superseding it.
- **Note on FR-SUM-03's rewrite:** with both rule edits (G-76) and promotions (G-79) gone, its enumeration would have been left citing only FR-RT-02. It now names **candidate authorship (FR-CAND-04)** and **library-recipe authorship** explicitly. This is a clarification, not a new requirement — FR-AUTH-13 already required exactly those two to be reattributed to the placeholder.

---

## Part P — Derived-artifact resync after the attribution cuts (2026-08-16)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I through O. Two separate approvals were given: one for
`app_user_stories.md`, one for the `requirements.md` traceability matrix.

This Part adds **no new decision.** Every change below propagates a decision
already taken (G-74, G-75, G-76, G-79) into a derived artifact that was missed
when that decision landed. Recorded as a numbered gap rather than a silent edit
because the artifacts are frozen and the edits are not reversible by inspection.

### G-80 · Four user stories and the traceability matrix still asserted removed behaviour
- **Gap:** The attribution and shopping cuts amended the requirement rows they
  touched but left two classes of derived artifact behind.

  **(a) `app_user_stories.md`.** **US4** listed five kinds of content to
  reattribute on user removal — "candidates, library recipes, definitive
  selections, rule edits, shopping list items" — of which **three no longer
  carry an author at all**: definitive selections (G-79), rule edits (G-76) and
  shopping list items (G-75). **US16** asked for a summary showing "who made
  them definitive", which *is* FR-SUM-02, removed by G-79. Both stories
  therefore promised behaviour the MVP will not have.

  **(b) `requirements.md` §13 traceability matrix.** Three rows cited
  requirement ids that had been removed: US16 → `FR-SUM-02` (G-79), and
  US22 / US23 → `FR-SHOP-11` (G-74). The matrix disagreed with the requirement
  rows above it, which correctly carry the strike-through.

- **Decision:** Strike the affected clauses in US4 and US16 inline, annotated
  with the gap that removed each one. Drop the three dead ids from the
  traceability matrix. Add a note to §13 recording that removed requirements are
  **dropped** from the matrix rather than struck, so the convention is written
  down rather than inferred.

- **Reasoning:** The convention was already set and simply not applied
  consistently. **G-68 dropped `FR-LIB-06` from the US17 and US18 matrix rows
  when it removed that requirement**; G-74 and G-79 struck their requirement
  rows but never cleaned the matrix. Applying the existing rule retroactively is
  the smallest change that makes the document self-consistent, and it is why
  this is bookkeeping rather than a decision.

  The user stories are handled the other way round — struck **inline** rather
  than dropped — following the FR-LIB-06 / FR-SHOP-11 / G-75 precedent, because
  a story is a historical record of what was asked for. What the household
  originally wanted is worth keeping visible; what the MVP will build is what
  the annotation clarifies. A matrix row, by contrast, is a pure index with no
  historical value, so a dead entry in it is simply wrong.

- **Requirements:** **None amended.** No `FR-*`/`NFR-*` row changes in this
  Part. `docs/app_user_stories.md` US4 and US16 amended;
  `docs/requirements.md` §13 matrix rows US16, US22 and US23 amended plus a
  convention note added. Propagates G-74, G-75, G-76 and G-79; supersedes
  nothing.

- **Not changed, and why:** `docs/coverage_analysis.md` was checked row by row
  and is already current — its US4 and US16 rows both record the amendments, and
  its gap index carries G-74 through G-79 correctly. Only its closing
  "G-01 to G-79, Parts A–O" counter needed advancing.

- **Correction to Part L's flag.** Part L predicted this desync but named the
  wrong artifacts: it flagged `coverage_analysis.md` and `app_user_stories.md`
  **US26** as un-synced for G-76. Both are in fact clean — US26 makes no
  attribution claim. The stories that drifted are **US4** and **US16**.

---

## Part Q — Repointing a reference into a deleted document (2026-08-16)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I through P. Granted for `coverage_analysis.md` only.

Like Part P, this Part adds **no new decision.** It repairs one cross-reference
that the owner's deletion of the working review records would otherwise have
left pointing at nothing.

### G-81 · The `NFR-AI-01` open question deferred to a document that no longer exists
- **Gap:** `docs/coverage_analysis.md` §4 closed with the project's one
  outstanding human-owned question — `NFR-AI-01` requires an *enforcing* path for
  the AI cost cap, but AWS Budgets only alert, they do not stop spend (G-70) —
  and then deferred the detail with "See `access_patterns_review.md` §7". The
  owner deleted `access_patterns_review.md` and `data_structure_review.md` on
  2026-08-16, having extracted their durable content into `docs/data_model.md`.
  **The question is still open**, so unlike the other surviving references to
  those files this one was not merely historical: it pointed a reader at the
  reasoning for a live decision, and the reasoning was about to vanish.

- **Decision:** Make the paragraph **self-contained** — state the question, its
  cause and its one code consequence inline — and track it against
  **`feature_list.json` #17 `ai_lambda`**, the feature whose implementation the
  answer changes. The `ai` Lambda is already `blocked` on architecture P4, so the
  question now sits with the work that cannot start without it.

- **Reasoning:** An open question needs an owner and a home, and a review
  document was never a good home for either — it is a working record, deleted
  when the work finishes, which is exactly what happened. The backlog entry is
  durable, is read at the start of every session via `init.sh`, and sits next to
  the code that depends on the answer. Restating the question inline rather than
  adding a second pointer also avoids recreating the same failure one level
  further along.

  Recorded as a numbered gap rather than a silent edit only because
  `coverage_analysis.md` is frozen. **Nothing about the question itself changed.**

- **Requirements:** **None amended.** No `FR-*`/`NFR-*` row changes.
  `docs/coverage_analysis.md` §4 amended; `feature_list.json` #17
  `blocked_reason` extended to carry the open question. Supersedes nothing.

- **Deliberately not changed:** three further references to the deleted review
  documents remain in **this file**, at the Part I (`G-70`), Part K and Part L
  entries. They are **historical citations inside dated records** — accurate
  statements about where reasoning lived when each decision was taken, not
  live pointers a reader must follow. Rewriting them would falsify the record.
  A dangling reference in a historical log is correct; one attached to an open
  question is not. That distinction is the whole of this Part.

---

## Part R — The ingredient-category set moves to one axis (2026-08-24)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I through Q. Granted for `requirements.md` only, and for
the single enumeration named below.

### G-82 · `vegetarian` is a diet label in a list of ingredients (amends G-69)
- **Gap:** `FR-RULE-04` enumerates the ingredient categories as *"(meat, fish,
  carbohydrates, legumes, vegetarian, …)"* — four terms naming a predominant
  **ingredient**, one naming a **diet**, and an open ellipsis. Because a recipe
  stores exactly one *predominant* category (`FR-LIB-03`, `G-69`), the mixed axis
  gives many dishes two equally valid filings: a chickpea curry is both `legume`
  and `vegetarian`, pasta al pesto both `carbohydrate` and `vegetarian`.
  `specs/recipe_model/design.md` §4 closed the ellipsis at exactly the five named
  terms and raised the ambiguity as its gate question 1 rather than resolving it.
  The owner then added `eggs` — an addition **inside** the ellipsis, needing no
  lift — which sharpened the defect instead of settling it: with `eggs` present,
  `vegetarian` was the only member of the set not naming an ingredient, and
  vegetable-predominant dishes (menestra, gazpacho, crema de calabaza) still had
  no home of their own.

- **Decision:** `vegetarian` is **struck** from the set and replaced by
  `vegetable`. The closed set becomes **meat, fish, carbohydrate, legume,
  vegetable, eggs** — six members, every one of them an ingredient. A dish is
  still filed under whichever single member predominates.

- **Reasoning:** The set's purpose is a weekly count per category
  (`FR-RULE-04`) that is verifiable against each recipe's stored value
  (`FR-AI-04`). A count is only verifiable if the categories partition the
  dishes, and a diet label cannot: it overlaps every plant-based member of the
  list by construction, so the same week yields different counts depending on
  which of two correct answers each author picked. `vegetable` sits on the same
  axis as the other five, removes the overlap, and gives the household the
  quota it actually lacked — vegetable-forward meals per week — which
  `vegetarian` could never express, since it also counted the pasta.

  **The accepted cost is stated deliberately:** a *"vegetarian meals per week"*
  rule is no longer expressible. Vegetarian dishes now distribute across
  `legume`, `carbohydrate`, `vegetable` and `eggs`, and no single count
  recovers them. `prototypes/wireframe/Sobremesa.dc.html` shows exactly that
  rule in its rules panel; it is a throwaway prototype (feature 20 replaces it)
  and was left untouched. The owner judged the diet quota worth less than an
  unambiguous, countable axis.

- **Requirements:** `FR-RULE-04` (amended — the literal enumeration only).
  **Amends G-69**, which drew the set from `FR-RULE-04` without questioning its
  composition; G-69's decision, its "lentejas con chorizo" reasoning and its
  supersession of G-63 all stand unchanged. Supersedes nothing.

- **Deliberately not changed:** `FR-LIB-03`, `FR-LIB-04` and `FR-AI-04` all
  reach the set **by reference** ("the fixed category set of FR-RULE-04") rather
  than enumerating it, so they inherit this edit with no text change. `eggs` is
  **not** added to `FR-RULE-04`'s enumeration either: the requirement says "at
  minimum" and ends in an ellipsis, so an addition needs no amendment, while
  removing a term the frozen text names by hand does. The literal, final list
  stays where `docs/architecture.md` §2.1 puts it — decided in a spec.

---

## Part S — Breached-password blocklist dropped from the MVP (2026-08-26)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I through R. Granted for `requirements.md` only, and for
the single clause named below.

### G-83 · The breached-password blocklist is deferred, not shipped in the MVP (amends G-30, G-60)
- **Gap:** Feature 9 `password_policy`'s spec (`specs/password_policy/`) reached
  the point of implementing FR-AUTH-15's blocklist clause and surfaced a real
  constraint the requirement never accounted for: `docs/architecture.md` §3.1
  rule 1 and §3.1's "No IO" statement for `domain/` forbid both a network call
  (e.g. Have I Been Pwned's k-anonymity API) and a bundled data file read at
  import time, and `backend/core`'s `pyproject.toml` fixes `dependencies = []`
  (feature 1, done) — so no third-party corpus library is available either.
  The only form left for a pure-domain, zero-dependency module is a hand-typed
  Python literal, and a hand-typed list is necessarily small and arbitrary —
  not a real breach corpus, and not markedly better than the English-only list
  G-60 already rejected as missing the point for a Spanish user base.
- **Decision:** The blocklist-rejection clause of FR-AUTH-15 is **struck** from
  the MVP. The length floor, the absence of composition rules, and the absence
  of forced rotation — the rest of FR-AUTH-15 — are unaffected and still ship
  in feature 9. G-60's Spanish-inclusivity requirement is now moot for the MVP
  since it amended the clause being struck; it is not itself struck, since it
  would re-apply in full the moment the blocklist ships for real.
- **Reasoning:** A thin, hand-curated literal would satisfy FR-AUTH-15's letter
  while being honestly no better than the English-only list G-60 already
  judged insufficient — shipping it would be checking a box, not adding a real
  control. The right shape for a genuine blocklist is an **injectable**
  dependency (the same pattern already used for `Clock`, `docs/architecture.md`
  §1.2.2/§3.1 rule 6: a port plus a sanctioned default, chosen by `wiring.py`
  not by `domain/`), fed by a real corpus (a maintained wordlist, or HIBP's
  k-anonymity API) through an adapter — infrastructure that does not exist
  yet and is out of scope for a tier-1, architecture-independent feature. The
  owner chose to defer the whole control rather than ship a token version of
  it now and revisit later.
- **Requirements:** `FR-AUTH-15` (amended — blocklist clause struck).
  **Amends G-30** (which specified the blocklist as part of the NIST alignment)
  and **G-60** (whose Spanish-inclusivity fix to that clause is now dormant,
  not deleted, pending the deferred future work). Supersedes neither — both
  remain the correct record of what a real implementation must do when this
  ships.
- **Future work (not scheduled, no feature id assigned):** re-introduce the
  blocklist as an injectable check with a real corpus once an adapter layer
  exists (post feature 14 `persistence_ports` / feature 15 `auth_flow`, once
  **P2** is decided). Revert this strike when that lands.

---

## Part T — Prompt wording gets a version identity (2026-08-26)

Directed by the requirements owner, overriding the freeze in `CLAUDE.md` in the
same manner as Parts I through S. Granted for `requirements.md` only, and for
the single addition named below.

### G-84 · Prompt wording has no version identity or config-selected activation
- **Gap:** `ai_prompt.py`'s `build_instructions()` (feature 11, implemented,
  pending sign-off) compiles `HEALTHY_BALANCED_INSTRUCTION`, `OUTPUT_LANGUAGE`
  and `CONFIGURED_SERVINGS` as plain module constants with no version identity
  — every generation uses whatever the current source tree happens to contain.
  `FR-AI-06`, `FR-AI-07` and `FR-AI-13` specify what the instructions must say,
  but nothing says how that wording is allowed to change over time, or how a
  past AI-generated recipe (`G-05`'s recipe snapshot) could be traced back to
  the exact wording that produced it. `G-64` solved this shape of problem for
  the servings count alone, marking it deployment configuration; the
  instruction text itself was left as ordinary source code on the ordinary
  code-review lifecycle.
- **Decision:** New requirement `FR-AI-14`: prompt instructions are
  **versioned**; the prompt version used for a given generation is
  **deployment configuration** (same class of config as `FR-AI-13`'s servings
  count), selected explicitly rather than implied by "whatever HEAD currently
  says"; retired versions are retained, not deleted.
- **Reasoning:** Generalizes `G-64`'s reasoning: deployment config lets prompt
  wording change without a full spec/design/implementer/reviewer cycle per
  tweak, while keeping the change explicit and auditable instead of silent
  code drift. Retaining retired versions gives traceability symmetric to
  `G-05`'s snapshot decision — a recipe's snapshot is stable, but nothing
  today records which prompt wording generated it, which matters if a bad
  wording change needs rolling back without touching code, or someone asks
  later why the AI suggested what it did.
- **Requirements:** New `FR-AI-14`. Does not amend `FR-AI-06`, `FR-AI-07` or
  `FR-AI-13` — their content requirements are unchanged; this adds a
  versioning/config requirement on top of them.
