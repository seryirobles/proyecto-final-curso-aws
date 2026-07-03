# Coverage Analysis — User Stories vs. Requirements

> Original review date: 2026-07-03. Method: each story in `app_user_stories.md`
> was checked against `requirements.md`, first for **existence** of coverage,
> then for **completeness** — including UX aspects a story implies but does not
> spell out (loading/error/empty states, conflict handling, navigation). Feature
> scope was deliberately kept to what the stories say; anything that would add a
> feature was raised as a **PEND** question instead of a requirement.
>
> **Update, same day:** the stakeholder answered PEND-05, -07, -09, -10, -11,
> -12 and -13, and three of those answers (-07, -09, -10) added **new user
> stories** (next-week planning, admin user removal, shopping-item check-off),
> bringing the total from 24 to **27**. The table below reflects the **final**
> state after those additions.
>
> **Second update, same day:** the stakeholder then confirmed the six
> remaining working assumptions (PEND-01, -02, -03, -04, -06, -08) as final,
> exactly as documented.
>
> **Third update, same day:** with all scope merged, a **post-integration
> re-scan** looked specifically for interactions between the newly added
> features and the pre-existing requirements. It found 10 further gaps, all
> resolved (G-42 to G-51), and raised one new business question (**PEND-14**,
> combined two-week shopping view).
>
> **Fourth update, 2026-07-04:** the stakeholder resolved PEND-14 — a
> **single shared shopping list**, populated by a **button** with the
> ingredients of **definitive-only** meals in the current week (today onward)
> and the next week (G-52; US23 rewritten) — and refined it: at week close the
> list **clears itself of that week's bought items**, keeping the items from
> the former next week (G-53; US24 extended).
>
> **Fifth update, 2026-07-04:** a **second post-integration re-scan** examined
> the interactions created by the shopping-list decisions and the two-live-week
> model. It found 8 further gaps, all resolved (G-54 to G-61), and raised one
> new business question (**PEND-15**, accessibility target).
>
> **Sixth update, 2026-07-04:** PEND-15 resolved — **browser-default
> accessibility only**, recorded as scope-exclusion FR-UX-07 (G-62). A final
> **exhaustive sweep** with no target count (Part H of
> `gaps_and_resolutions.md`) found two semantic gaps in core features and
> three smaller fixes (G-63 to G-67), raised **zero** new business questions,
> and recorded the items examined and rejected as beyond-MVP. **Nothing is
> open.** The reasoning behind every gap and confirmation is in
> `gaps_and_resolutions.md`.

## 1. Headline findings

1. **Stale story numbering (fixed).** `requirements.md` had originally been
   written against an earlier version of the stories, and then three more
   stories were added mid-review. All `US#` references and the traceability
   matrix are now aligned to the current, final 27-story file. (G-03)
2. **The first-login/reset-password story was uncovered — and contradicted.**
   The old FR-AUTH-04 stated that *nobody* can change their own password
   through the application, incompatible with the mandatory set-password flow
   the story requires. FR-AUTH-04 was amended and FR-AUTH-10/-11 added. (G-09,
   G-10)
3. **19 completeness gaps** were identified across otherwise-covered stories
   in the initial pass and resolved with new or amended requirements (G-11 to
   G-27).
4. **7 stakeholder questions were resolved same-day** (G-28 to G-35),
   adding a second live "next week", user removal with content reattributed to
   an "unknown user", shopping-item check-off, an explicit browser support
   matrix, library search/filter, and a NIST-aligned password/session policy.
5. **The remaining 6 questions were confirmed same-day** (G-36 to G-41): the
   "healthy/balanced" definition, rule-edit governance, the AI cost cap, the
   shopping-list unit approach, the admin-account bootstrap/recovery model, and
   the archive retention policy are all now final as originally documented.
6. **The post-integration re-scan found 10 more gaps** (G-42 to G-51), the
   most consequential being: recipe ingredient units were never constrained to
   the shopping list's fixed unit list, silently defeating auto-aggregation
   (G-48); mid-week generation would spend capped AI budget on days already
   past (G-45); multiple admins were supported but impossible to create, and
   admin removal was undefined (G-43); usernames were never required to be
   unique (G-42). All are resolved; one new business question was raised
   (PEND-14, combined two-week shopping view).
7. **PEND-14 was resolved on 2026-07-04** (G-52): a single shared shopping
   list, populated on button press from definitive-only meals of the current
   week (today onward) plus the next week — replacing the two per-week lists
   and the automatic re-sync trigger. US23 was rewritten to match.
8. **The shopping list self-cleans at week close** (G-53, same day): checked
   (bought) items of the closing week are cleared automatically — unless still
   required by the former next week, whose items always remain — with the
   archive snapshot taken before the cleanup. US24 was extended to match.
9. **The second re-scan found 8 more gaps** (G-54 to G-61), the most
   consequential being: the shopping-button sync had no concurrency/idempotency
   protection, unlike AI generation (G-54); week rollover had accreted into a
   five-step transaction with no failure semantics (G-61); exact-string name
   matching quietly fragmented shopping aggregation (G-56); and nothing made
   the active week visible, so bulk actions could target the wrong week
   (G-57). All are resolved; one new business question was raised (PEND-15,
   accessibility target).
10. **The final exhaustive sweep found two semantic gaps in core features**
   (G-63 to G-67): nothing defined how a meal gets an ingredient category —
   the enforcement mechanism of the rules' central lever was undefined
   (resolved: deterministic pins/disabled days; AI best-effort category
   counts; no stored category) — and AI recipes had no servings assumption,
   making shopping quantities arbitrary (resolved: configured serving count in
   every prompt). Plus: re-seeded admin credentials are temporary, library-only
   generation fails with a clear message, and definitive meals stay editable
   until archival. PEND-15 was closed as **browser-default accessibility
   only** (G-62, FR-UX-07). Zero new business questions.

## 2. Story-by-story coverage

Verdict meaning — **Full**: covered as written; **Full (fixed)**: coverage was
missing or incomplete and has been fixed in this revision; **Full (new)**:
story added in the same-day stakeholder round and covered from the start.

| US | Story (abridged) | Requirements | Verdict | Gaps found |
|----|------------------|--------------|---------|------------|
| US1 | Admin-exclusive view to create/manage users, nothing else | FR-AUTH-01, -03, -05, -06, -07, -12 | Full (fixed) | No requirement said the admin can *see* the accounts to manage (G-11). |
| US2 | Admin logs in with username+password; no register / password change | FR-AUTH-01, -02, -03, -04, -07, -16, NFR-SEC-04 | Full (fixed) | FR-AUTH-04 amended for compatibility with US27 (G-09). Login brute-force protection was unspecified (G-12). Password policy and session lifetime resolved (G-30, G-31). |
| US3 | Admin can reset a user's password | FR-AUTH-01, -05, -11 | Full (fixed) | Was only implicit and mis-attributed to US1 (G-03). Post-reset semantics (temporary password, session invalidation) were undefined (G-10). |
| US4 | Admin can remove a user; content reattributed to "unknown user" | FR-AUTH-12, -13, -14, FR-SUM-03 | Full (new) | Added to close PEND-09. Session invalidation on removal and attribution fallback specified (G-29). |
| US5 | User logs in with username+password; no register / password change | FR-AUTH-01, -02, -03, -04, -16, NFR-SEC-04 | Full (fixed) | Same as US2. |
| US6 | Usable on computer and mobile via website | FR-UX-02 | Full (fixed) | Browser/device support matrix was undefined; now explicit (Chrome, Firefox, Edge, Safari, Brave) per stakeholder answer (G-33). |
| US7 | Current week's menu, Mon–Sun, lunch & dinner | FR-MENU-01, -02, -06 | Full (fixed) | What happens at week rollover was undefined; now the former next week becomes current (G-15, G-28). |
| US8 | See and plan next week's menu in advance | FR-MENU-01, -06, -07 | Full (new) | Added to close PEND-07 — shopping needs to happen before the week starts. Given identical functionality to the current week (G-28). |
| US9 | Click a meal → detailed recipe (ingredients, tools, procedure) | FR-MENU-04, -05, FR-LIB-03 | Full (fixed) | The story is written from the week-menu view, but the same detail must open wherever a meal appears (summary, library, archive); this was unspecified (G-14). |
| US10 | Add/edit/remove day candidates: from library, from scratch, or AI | FR-MENU-03, FR-CAND-01, -02, -03, -07, FR-RT-02 | Full | Snapshot semantics already resolved (G-05). |
| US11 | Add a meal from the week's menu to the library | FR-CAND-06 | Full (fixed) | Duplicate behaviour was undefined (meal may itself come from the library): now always a new entry + same-name warning (G-26). |
| US12 | AI generates the whole week (library-only / AI-only / mix) as candidates | FR-AI-03, -04, -08, -09, -11, -12, -13, NFR-AI-01 | Full (fixed) | Target slots and interaction with existing candidates/definitives were undefined (G-18). Progress and per-slot failure UX were undefined (G-19). Now generalized to either live week (G-28). Category-count enforcement semantics defined (G-63); servings assumption fixed (G-64); insufficient-library failure surfaced clearly (G-66). |
| US13 | Confirmation prompt with current rules + this-run-only edit | FR-AI-04, -05, FR-RULE-05 | Full | Per-run override already resolved (G-06); dropdown-only editing made explicit in FR-AI-05. |
| US14 | Generated meals balanced and healthy | FR-AI-06 | Full | Qualitative prompt instruction + rules-based quantitative balance confirmed as final, no medical/nutritional model in scope (G-36). |
| US15 | See anyone's candidates; select one as definitive | FR-MENU-03, FR-CAND-04, -05, -08, FR-RT-02 | Full (fixed) | No way to *undo* a definitive selection existed — only replacing it with another candidate; now FR-CAND-08 (G-16). Concurrent selection already resolved via last-write-wins (G-07). Definitive meals clarified as editable until archival (G-67). |
| US16 | Read-only weekly summary + who made each meal definitive | FR-SUM-01, -02, -03 | Full (fixed) | Requires storing the promoting user; implied by FR-SUM-02. Attribution now falls back to "unknown user" if that account was removed (G-29). |
| US17 | AI single recipe from specs, or from a library reference + specs | FR-CAND-02, -03, FR-LIB-03, -05, -06, FR-AI-01, -02, -08, -09, -10, -12, -13, NFR-AI-01 | Full (fixed) | No accept/discard/regenerate step existed — a bad generation would land directly in the plan (G-17). Loading/failure UX undefined (G-19). Units constrained (G-48), difficulty scale fixed (G-49), servings assumption fixed (G-64). |
| US18 | See all library recipes; add/edit/remove them | FR-CAND-03, -07, FR-LIB-01, -02, -04, FR-RULE-07, FR-RT-02 | Full (fixed) | Deleting a recipe pinned by a general rule left the rule dangling (G-20). Search/filter at scale, previously flagged as a scope question, is now in scope (G-34). |
| US19 | See other users' week-menu changes in real time | FR-AI-09, FR-RT-01, -02, -03 | Full (fixed) | Connection-loss / reconnection behaviour was unspecified — without it "real time" silently degrades to "stale" (G-22). Now applies to both live weeks (G-28). |
| US20 | App in Castilian Spanish | FR-AI-07, FR-UX-01, -03 | Full (fixed) | Only the UI and AI output were covered; validation/error/system messages and date & number formats were not (G-23). |
| US21 | Shopping list with item name and quantity | FR-SHOP-01, -05 | Full (fixed) | Fixed-unit-list approach confirmed as final; exact unit enumeration left as an implementation detail (G-39). Now a **single shared list** spanning the shopping horizon (G-52). |
| US22 | Add/edit/remove shopping items | FR-SHOP-02, -04, -06 | Full (fixed) | What happens when a user edits an *auto-generated* item and the list re-syncs was undefined (G-21). |
| US23 | Button adds ingredients of definitive meals (current week from today + next week) | FR-SHOP-03, -04, -05, -06, FR-LIB-05 | Full (fixed) | Re-sync trigger was undefined (G-21, initially automatic); story rewritten by the stakeholder on 2026-07-04 — now an explicit button, definitive-only, current-week-forward + next week (G-52). |
| US24 | Check off shopping items as bought; bought items self-clear at week close | FR-SHOP-07, -08, -09 | Full (new) | Added to close PEND-10, with the specific below/greyed-out layout and re-check-safe re-sync behavior the stakeholder specified (G-32). Extended 2026-07-04: rollover clears the closed week's bought items, sparing everything the former next week needs (G-53). |
| US25 | Record of all past weeks, accessible any time | FR-ARCH-01, -02, -03, -04 | Full (fixed) | No requirement described *how* past weeks are found/navigated (G-27). Retention/cold storage resolved (G-13) and confirmed as final (G-41). |
| US26 | Shared general generation rules, list in own section, dropdown-only | FR-MENU-06, FR-AI-04, -11, FR-RULE-01, -02, -03, -04, -06, -07, FR-LIB-04 | Full (fixed) | Nothing prevented contradictory rule sets (e.g. category counts exceeding available slots, pin on a disabled day) (G-20). Free-for-all editing (no governance role) confirmed as final (G-37). Category enforcement semantics defined: deterministic pins/disabled days, AI best-effort counts, fixed category list (G-63). |
| US27 | Set my password at login on first login / after admin reset | FR-AUTH-04, -10, -11, -15 | Full (fixed) | **Previously uncovered and contradicted by FR-AUTH-04** (G-09). Temporary-password lifecycle defined (G-10). Concrete password policy now specified (G-30). |

## 3. Gaps resolved

Full reasoning per gap in `gaps_and_resolutions.md`.

| Gap | Area | Summary | Requirement(s) |
|-----|------|---------|----------------|
| G-03 | Traceability | Story renumbering drift (twice) | Whole-document renumbering; FR-AUTH-05 |
| G-09 | Auth | US27 uncovered; contradicted old FR-AUTH-04 | FR-AUTH-04 (amended), FR-AUTH-10 |
| G-10 | Auth | Admin-assigned passwords: lifecycle & session invalidation | FR-AUTH-11 |
| G-11 | Auth/UX | Admin needs a visible account list to "manage users" | FR-AUTH-12 |
| G-12 | Security | Login brute-force protection unspecified | NFR-SEC-04 |
| G-14 | Menu/UX | Recipe detail reachable from every meal occurrence | FR-MENU-05 |
| G-15 | Menu | New current week starts with content only via rollover carry-over | FR-MENU-06 |
| G-16 | Candidates/UX | Definitive selection could not be undone | FR-CAND-08 |
| G-17 | AI/UX | Preview + accept/discard/regenerate for single-recipe AI | FR-AI-10 |
| G-18 | AI | Whole-week generation target slots & non-destructive add | FR-AI-11 |
| G-19 | AI/UX | Progress states and per-slot failure surfacing | FR-AI-12 |
| G-20 | Rules | Rule-set satisfiability; deleting a pinned recipe | FR-RULE-07 |
| G-21 | Shopping | Re-sync trigger; edits to auto items preserved | FR-SHOP-06 |
| G-22 | Real-time/UX | Connection-loss indicator, reconnect & re-sync | FR-RT-03 |
| G-23 | i18n | es-ES for *all* messages plus date/number formats | FR-UX-03 |
| G-24 | UX | Confirmations for destructive actions | FR-UX-04 |
| G-25 | UX | Empty states and loading states | FR-UX-05 |
| G-26 | Library | "Save to library" duplicate behaviour | FR-CAND-06 (amended) |
| G-27 | Archive/UX | Navigation of past weeks | FR-ARCH-04 |
| G-28 | Menu/Shopping | Second live week ("next week"), rollover carry-over | FR-MENU-01, -06, -07 and others |
| G-29 | Auth | User removal; "unknown user" attribution | FR-AUTH-12, -13, -14, FR-SUM-03 |
| G-30 | Auth | Password policy (NIST 800-63B) | FR-AUTH-15 |
| G-31 | Auth | Session lifetime | FR-AUTH-16 |
| G-32 | Shopping/UX | Check-off items, layout, re-sync-safe | FR-SHOP-07, -08 |
| G-33 | UX | Browser/device support matrix | FR-UX-02 (amended) |
| G-34 | Library | Search and filter | FR-LIB-04 |
| G-35 | — | Scale assumption confirmed | (none; confirms NFR-AI-01, NFR-FIN-02) |
| G-36 | AI | "Healthy/balanced" definition confirmed | FR-AI-06 (unchanged) |
| G-37 | Rules | Rule-edit governance confirmed (free-for-all) | FR-RULE-06 (unchanged) |
| G-38 | AI/Cost | €50/month AI cap confirmed; per-user cap left to implementation | NFR-AI-01 |
| G-39 | Shopping | Fixed-unit-list approach confirmed; enumeration left to implementation | FR-SHOP-03 |
| G-40 | Auth | Admin bootstrap/recovery model confirmed | FR-AUTH-07, -08 (unchanged) |
| G-41 | Archive | Retention/cold-storage policy confirmed | FR-ARCH-03 (unchanged) |
| G-42 | Auth | Username uniqueness (active accounts); reuse after removal | FR-AUTH-17 |
| G-43 | Auth | Admin lifecycle: IaC-only provisioning, reset-each-other, no in-app removal | FR-AUTH-18 |
| G-44 | Shopping/UX | Quantity change on a checked item: flagged, never unchecked | FR-SHOP-08 (amended) |
| G-45 | AI/Cost | Current-week generation targets today-onward slots only | FR-AI-11 (amended) |
| G-46 | Library/UX | Search/filter in every library-picking flow (candidates, AI reference, rule pinning) | FR-LIB-04 (amended) |
| G-47 | Real-time | Library changes added to the real-time broadcast | FR-RT-01 (amended) |
| G-48 | Recipes/Shopping | Ingredient units constrained to the fixed unit list in all authoring flows | FR-LIB-05 |
| G-49 | Library | Difficulty as predefined scale; cuisine free text with suggestions | FR-LIB-06 |
| G-50 | Candidates/UX | Candidates display their author | FR-CAND-04 (amended) |
| G-51 | Auth | Any admin-assigned password (change or reset) is temporary | FR-AUTH-11 (amended) |
| G-52 | Shopping | Single shared list; button-triggered, definitive-only, current-week-forward + next week | FR-SHOP-01, -03, -05, -06, FR-ARCH-02 (amended); US23 rewritten |
| G-53 | Shopping | Rollover self-clean: closed week's bought items removed, former-next-week items kept | FR-SHOP-09; FR-MENU-06, FR-ARCH-02 (amended); US24 extended |
| G-54 | Shopping | Button sync idempotent & serialized under concurrent presses | FR-SHOP-10 |
| G-55 | Shopping/UX | Manual/auto same name+unit rows grouped and marked as likely duplicates | FR-SHOP-11 |
| G-56 | Shopping/Library | Case-/accent-/whitespace-insensitive matching for aggregation and cuisine values | FR-SHOP-03, FR-LIB-06 (amended) |
| G-57 | UX | Active week always labelled with date range; generation prompt shows target week | FR-UX-06; FR-AI-05 (amended) |
| G-58 | Auth | "unknown user" placeholder name reserved; distinct rendering | FR-AUTH-17 (amended) |
| G-59 | Candidates/UX | Duplicate-candidate warning in a slot | FR-CAND-01 (amended) |
| G-60 | Security | Password blocklist must include common Spanish passwords | FR-AUTH-15 (amended) |
| G-61 | Menu/Reliability | Rollover as an atomic, idempotent, re-runnable job | FR-MENU-08 |
| G-62 | UX/Scope | Accessibility: browser defaults only (stakeholder decision, PEND-15) | FR-UX-07 |
| G-63 | Rules/AI | Ingredient-category semantics: deterministic pins/disabled days; AI best-effort category counts; fixed category list | FR-AI-04, FR-RULE-04 (amended) |
| G-64 | AI/Shopping | Configured servings count in every AI prompt | FR-AI-13 |
| G-65 | Auth | Re-seeded bootstrap credential is temporary | FR-AUTH-08 (amended) |
| G-66 | AI/UX | Library-only/mix generation with insufficient library fails with a clear message | FR-AI-12 (amended) |
| G-67 | Candidates | Definitive meals stay editable; content freezes only at archival | FR-CAND-05 (amended) |

## 4. Open questions remaining

None. Every question raised across all review passes is resolved or confirmed
(PEND-01 to PEND-13 on 2026-07-03; PEND-14 and PEND-15 on 2026-07-04). See
`gaps_pending_stakeholders.md` for the historical record and
`gaps_and_resolutions.md` (G-01 to G-67, Parts A–H, including the
examined-and-rejected list in Part H) for the reasoning.
