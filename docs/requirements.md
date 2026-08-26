# Requirements Specification — Collaborative Weekly Meal Planner

> Derived from `app_user_stories.md` (functional team) and the common project
> requirements in `cloud_aws_enunciados-proyecto-final/` (AWS final project,
> "libre" option). Each requirement is traceable to the originating user story
> (`US#`, numbered by line order in `app_user_stories.md`, 27 stories as of
> 2026-07-03). The full story-by-story coverage assessment is in
> `coverage_analysis.md`; decisions taken to fill ambiguities are documented in
> `gaps_and_resolutions.md` (G-xx). Business decisions are tracked in
> `gaps_pending_stakeholders.md` (PEND-xx): **all confirmed** by the
> stakeholder — the last, PEND-15 (accessibility: browser defaults only), on
> 2026-07-04 (see G-62).

## 1. Product summary

A web application (desktop + mobile) where a fixed set of **users**, created and
managed by an **admin**, collaboratively plan the meals of the **current week and
the next week** (Monday–Sunday, lunch and dinner, each with identical planning
features). Users propose candidate meals per day, pick a definitive meal per
slot, maintain a shared recipe library, generate recipes and whole-week plans
with AI under shared rules, build a single shared shopping list for the days
ahead (with items checkable as they're bought), and consult an archive of past
weeks — all in Castilian Spanish, with changes reflected in real time between
users.

---

## 2. Roles and access control

| ID | Requirement | Source |
|----|-------------|--------|
| FR-AUTH-01 | The system shall support exactly two roles: **Admin** (user management) and **User** (meal planning). | US1, US2, US3, US5 |
| FR-AUTH-02 | Authentication shall be by **username + password** for both roles. | US2, US5 |
| FR-AUTH-03 | The system shall **not** offer public self-registration for any role. Users are created only by an admin. | US1, US2, US5 |
| FR-AUTH-04 | Neither admins nor users shall be able to change **their own** password through the application at will. The **only** exception is the mandatory set-password step at login when the account is new or its password has been reset (FR-AUTH-10). | US2, US5, US27 |
| FR-AUTH-05 | The Admin shall have an **exclusive view** restricted to user management: create users, change usernames, and change/**reset** user passwords. The admin shall have **no access** to any meal-planning feature. | US1, US3 |
| FR-AUTH-06 | Users shall have access to all meal-planning features but **no** access to the admin/user-management view. | US1 |
| FR-AUTH-07 | Exactly **one** Admin account shall be provisioned at deployment time (bootstrap). The system shall **support multiple admins** so they can reset each other, but only one is created initially. | US1, US2 (confirmed, see G-01, G-40) |
| FR-AUTH-08 | Admin account recovery shall be possible by **re-seeding** the bootstrap admin from its IaC-managed secret. A re-seeded credential is **temporary** like any admin-assigned password (FR-AUTH-11): it only reaches the mandatory set-password step (FR-AUTH-10). | (confirmed, see G-08, G-40, G-65) |
| FR-AUTH-09 | The application shall enforce HTTPS-only access and authenticated sessions; users shall be able to log out. | NFR/security |
| FR-AUTH-10 | When an account (user **or** admin) logs in for the **first time**, or after its password has been **reset by an admin**, the login screen shall force it to set a new password before granting access to the application. | US27 (see G-09) |
| FR-AUTH-11 | Passwords assigned by an admin — at account creation, password **change**, or **reset**, in every case — shall be **temporary**: valid only to reach the mandatory set-password step (FR-AUTH-10), never to enter the app directly. An admin password reset shall **invalidate all active sessions** of the affected account. | US3, US27 (see G-10, G-51) |
| FR-AUTH-12 | The admin view shall display a **list of all accounts** (username, role, pending set-password status) from which the management actions of FR-AUTH-05 and the removal action of FR-AUTH-13 are launched. | US1, US4 (see G-11) |
| FR-AUTH-13 | An admin shall be able to **remove** a user account. All content previously authored by that account — candidate meals, library recipes, ~~definitive-meal promotions~~ (**removed** by G-79: none is stored) — shall be **retained** and **reattributed** to a generic **"unknown user"** placeholder rather than deleted or blocked from removal. ~~shopping-list items~~ — **removed from the list** by G-75: since G-72 a shopping-list item stores no author, so there is no attribution to reassign. ~~rule edits~~ — **removed** by G-76: rules carry no author. | US4 (resolves PEND-09, see G-29; amended by G-75, G-76) |
| FR-AUTH-14 | Removing a user shall immediately **invalidate all active sessions** of that account, consistent with the session-invalidation behavior of a password reset (FR-AUTH-11). | US4 (see G-29) |
| FR-AUTH-15 | The set-password step (FR-AUTH-10) shall enforce a password policy aligned with **NIST SP 800-63B**: minimum length of **10 characters** (up to at least 64, untruncated), **no** mandatory character-composition rules, **no** forced periodic rotation. ~~and rejection of passwords found on a common/breached-password blocklist. The blocklist shall include common Spanish-language passwords, not only English-centric lists.~~ — **removed from the MVP** by G-83: a domain-pure, zero-IO, zero-dependency check cannot draw on a real breached-password corpus, and the owner judged a hand-curated literal not worth shipping as the MVP's version of this control. Deferred to a future pass, once an adapter layer can supply a real corpus. | US27 (resolves PEND-05, see G-30, G-60; amended by G-83) |
| FR-AUTH-16 | User sessions shall expire after **12 hours of inactivity** or a **30-day absolute lifetime**, whichever comes first, requiring re-authentication thereafter. | US2, US5 (resolves PEND-05, see G-31) |
| FR-AUTH-17 | Usernames shall be **unique among active accounts**, validated on creation and rename. A **removed** account's username **may be reused**, since removal already detaches all attribution to the "unknown user" placeholder (FR-AUTH-13). The placeholder's name shall be **reserved** (never creatable as a username), and the placeholder shall render as a **distinct system label**, not as a regular account. | US1, US2, US5 (see G-42, G-58) |
| FR-AUTH-18 | Admin accounts shall be provisioned **only via IaC** (bootstrap/seeding, FR-AUTH-07/-08), never through the application. The admin view additionally allows an admin to **reset another admin's password** (never their own, FR-AUTH-04). Admin accounts shall **not** be removable through the application — FR-AUTH-13 applies to **user** accounts only. | US1, US3, US4 (see G-43) |

---

## 3. Week menus — structure and viewing (current & next)

| ID | Requirement | Source |
|----|-------------|--------|
| FR-MENU-01 | The system shall present **two live weeks** — the **current week** and the **next week** — each split into 7 days (Monday→Sunday) and, per day, two meal slots: **lunch** and **dinner**. | US7, US8 |
| FR-MENU-02 | "Current week" shall be computed as the ISO week (Monday–Sunday) in the **Europe/Madrid** timezone; "next week" is the ISO week immediately following it. | US7 (gap, see resolution G-02) |
| FR-MENU-03 | Each meal slot holds a list of **candidate** meals and at most one **definitive** meal. | US10, US15 |
| FR-MENU-04 | Clicking a meal shall open its detailed recipe: **ingredients (with quantities), tools, and procedure**. | US9 |
| FR-MENU-05 | The detailed recipe view (FR-MENU-04) shall be reachable from **every place a meal is displayed**: day candidates, definitive meals, the weekly summary, the library, and archived weeks. | US9 (see G-14) |
| FR-MENU-06 | At week rollover: the ending **current week** is archived (FR-ARCH-02) and becomes read-only; the former **next week** becomes the new **current week**, carrying over whatever candidates and definitives it already had; a new, empty **next week** is initialized; the shared shopping list is **cleared of all bought items** (FR-SHOP-09). Rules take effect only through generation (FR-AI-11) or manual planning — the new next week is never auto-populated. | US7, US8, US26 (see G-15, G-28, G-53; amended by G-73) |
| FR-MENU-07 | The current week and the next week shall offer **identical functionality**: candidates (Section 4), definitive selection, AI generation (Section 6), the weekly summary (Section 7), and application of the general rules (Section 8). Unless a requirement says otherwise, every requirement in those sections applies **independently to each live week**. Users shall be able to switch between viewing/planning the current week and the next week. | US8 (see G-28) |
| FR-MENU-08 | Week rollover (FR-MENU-06) shall be implemented as an **atomic, idempotent, re-runnable job**: its steps — archiving, shopping-list snapshot (FR-ARCH-02), promotion of next→current, initialization of the new next week, and shopping-list cleanup (FR-SHOP-09) — shall be safely retryable after a partial failure, without data loss, double-archiving, or double-cleanup. | US7, US8, US25 (see G-61) |

---

## 4. Candidates and recipe authoring

| ID | Requirement | Source |
|----|-------------|--------|
| FR-CAND-01 | A user shall be able to **add, edit, or remove** candidate meals for any day/slot, individually. Adding a candidate whose name matches an existing candidate in the same slot shall trigger a **duplicate warning** (same pattern as FR-CAND-06). | US10 (see G-59) |
| FR-CAND-02 | When adding/editing a candidate, the user shall choose one of three authoring methods: (a) pick an existing recipe from the **library**, (b) write a **new recipe from scratch**, or (c) **generate one with AI**. | US10, US17 |
| FR-CAND-03 | Creating/editing a recipe in the **library** shall reuse the same authoring flows as candidate authoring — specifically **writing from scratch** and **generating with AI** (FR-AI-01/-02, same UI and specification options: ingredients, tools, or a library recipe as reference). The "pick an existing library recipe" method does not apply here, since the target is the library itself. | US10, US17, US18 (see G-68) |
| FR-CAND-04 | A user shall be able to view candidate meals for a day regardless of whether they were created by themselves or by other users. Each candidate shall **display its author**. | US15 (see G-50) |
| FR-CAND-05 | A user shall be able to **promote a candidate to definitive** for its slot, replacing any previous definitive. A promoted (definitive) meal **remains editable** like any candidate; content edits propagate wherever it is shown — the summary stays a non-editing **view** (FR-SUM-01), not frozen content. | US15 (see G-67) |
| FR-CAND-06 | A meal shown in the week menu shall be **addable to the library** for reuse in other weeks. Saving always creates a **new** library entry from the meal's snapshot; the UI shall warn when a library recipe with the same name already exists. | US11 (see G-26) |
| FR-CAND-07 | A recipe added to a menu shall store a **snapshot** of the recipe content, so later library edits/deletes do not silently mutate existing or past menus. | US10, US18 (gap, see resolution G-05) |
| FR-CAND-08 | A user shall be able to **clear** the definitive selection of a slot, returning all its meals to candidate status. | US15 (see G-16) |

---

## 5. Recipe library

| ID | Requirement | Source |
|----|-------------|--------|
| FR-LIB-01 | Users shall see **all** recipes in the shared library, regardless of author. | US18 |
| FR-LIB-02 | Users shall be able to **add, edit, and remove** library recipes, using the same write-from-scratch and AI-generation authoring flows as candidate authoring (see FR-CAND-03). | US18 |
| FR-LIB-03 | A library recipe shall store: name, ingredients with quantities, tools, procedure, and exactly **one ingredient category** (`tipoAlimento`) — the category that **predominates** in the dish — chosen from the fixed category set of FR-RULE-04. The category shall be set in **every** recipe-authoring flow (from scratch or AI-generated, targeting a candidate or the library), selected via dropdown, with AI output instructed and validated to use that same fixed set. No cuisine, difficulty, or nutritional (kcal) attributes are stored. | US9, US17 (see G-69, G-68, G-36) |
| FR-LIB-04 | Users shall be able to **search** library recipes **by name** — in the library view and in **every flow where a library recipe is picked**: choosing a candidate from the library (FR-CAND-02a), selecting an AI reference recipe (FR-AI-02), and pinning a meal in a rule (FR-RULE-04). The library view shall additionally offer a **filter by ingredient category** (FR-LIB-03). No other attribute filters are offered. | US18, US26 (resolves PEND-12, see G-69, G-34, G-46, G-68) |
| FR-LIB-05 | Ingredient quantities in **all** recipe-authoring flows — from scratch or AI-generated, targeting a candidate or the library — shall use the **same fixed unit list** as the shopping list (FR-SHOP-03), selected via dropdown (AI output instructed and validated to use those units), so automatic aggregation always finds matching units. | US10, US18, US23 (see G-48) |
| FR-LIB-06 | ~~Difficulty scale and cuisine normalization.~~ **Removed** — cuisine and difficulty are no longer part of the product. The case-/accent-/whitespace-insensitive matching this requirement shared with shopping aggregation survives in FR-SHOP-03, which now owns it alone. | — (removed by G-68; was US17, US18, G-49, G-56) |

---

## 6. AI generation

| ID | Requirement | Source |
|----|-------------|--------|
| FR-AI-01 | The system shall generate a **single recipe** with AI from user inputs: ingredients and tools. | US17 (see G-68) |
| FR-AI-02 | The system shall alternatively generate a **single recipe** based on a chosen **library recipe as reference** plus extra user specifications. | US17 |
| FR-AI-03 | The system shall generate a **whole week's plan** with AI, for either the current or the next week, in one of three modes: (a) only library meals, (b) only newly AI-generated meals, or (c) a **mix**; all generated meals shall be added to their respective days/slots **as candidates**. | US12 |
| FR-AI-04 | Whole-week generation shall honor the active **general rules** (Section 8), regardless of which live week (current or next) is targeted. Pinned meals and disabled days are enforced **deterministically** by the system (FR-AI-11); ingredient-category counts are passed to the AI as **explicit prompt instructions** and are **verifiable after generation** against each recipe's stored category (FR-LIB-03). Since a recipe carries a single *predominant* category, these counts approximate the dish's composition and are **not** a nutritional measure. | US12, US13, US26 (see G-69, G-63) |
| FR-AI-05 | Before whole-week generation, the system shall show a **confirmation prompt** displaying the **target week** (current or next, with its Monday–Sunday date range) and the current general rules, offering to **edit them only for this generation run** (a per-week override that does not modify the shared rules; edited with the same dropdown-only controls as the shared rules, FR-RULE-03). | US13 (gap, see resolution G-06; amended by G-57) |
| FR-AI-06 | The AI prompt shall explicitly instruct the model to produce **healthy, balanced** menus that **vary protein sources**. Quantitative balance (how many meals per ingredient category) is enforced through the **general rules** (Section 8), not the prompt. Output is labelled **non-medical**. | US14 (confirmed, see G-36) |
| FR-AI-07 | AI output (recipe text, ingredients, procedure) shall be produced in **Castilian Spanish**. | US20 |
| FR-AI-08 | AI generation shall be **idempotent**: submitting the same generation request (same week, slot(s), and effective rules) more than once — whether by retry, double-click, or network re-send — shall **not** produce duplicate candidates nor duplicate AI invocations/charges. Idempotency shall be enforced via a generation key (e.g. a hash of the request) and conditional writes. | US12, US17 |
| FR-AI-09 | AI generation shall support **concurrency**: multiple users (and the per-slot tasks of a single whole-week generation) may run AI generations simultaneously without lost updates, double-writes, or corrupting each other's candidates. Per-slot results shall be written independently and the failure of one shall not abort the others. | US12, US17, US19 |
| FR-AI-10 | Single-recipe AI generation shall present the result as a **preview** the user can **accept, discard, or regenerate** (optionally adjusting the specifications) before it is saved as a candidate or library recipe. Each regeneration is a **fresh AI invocation** and therefore consumes budget against the global cost cap (NFR-AI-01); there is no per-user quota for it to count against. | US17 (see G-70, G-17) |
| FR-AI-11 | Whole-week generation shall target **every slot not disabled by the rules within the selected live week (current or next)**, **adding** candidates without removing existing candidates or definitive selections. A slot that **already holds a definitive meal shall be skipped entirely** — including when a rule pins a meal to it: an existing definitive **takes precedence over a pin**, and the skipped pin shall be reported to the user (FR-AI-12), never applied silently. Slots pinned by a rule and **not** holding a definitive receive the pinned library meal as their candidate. For the **current** week, only slots from the **current day onward** (Europe/Madrid) are targeted — no AI generation for days already past; past days remain manually editable. Weekly ingredient-category counts describe the **week's final state**, not the generated output: meals already present in the week count toward each category total, and generation supplies only the **remainder**, as far as the remaining targetable slots allow. | US12, US26 (see G-71, G-18, G-45) |
| FR-AI-12 | AI operations shall show a **progress/loading state** (per slot, for whole-week runs). Failures shall be surfaced **per slot** with a retry option and a friendly message in Castilian Spanish; partial results are kept (FR-AI-09). This includes the case where **library-only or mix generation cannot proceed for lack of suitable library recipes**: a clear message, never a silent partial result. | US12, US17 (see G-19, G-66) |
| FR-AI-13 | AI recipe generation (single and whole-week) shall target a **configured number of servings** (deployment configuration, e.g. 4 diners), stated explicitly in every prompt, so ingredient quantities are mutually consistent and usable by the shopping list. | US12, US17, US23 (see G-64) |
| FR-AI-14 | AI prompt instructions (FR-AI-06, FR-AI-07, FR-AI-13, and any future wording changes) shall be **versioned**. The prompt version used for a given generation shall be **deployment configuration**, explicitly selected rather than defaulting silently to whatever the code currently contains; retired versions shall be retained, not deleted, so a past AI-generated recipe can be traced back to the wording that produced it. | US12, US17, US23 (see G-84) |

---

## 7. Weekly summary, archive, and attribution

| ID | Requirement | Source |
|----|-------------|--------|
| FR-SUM-01 | The system shall provide a **read-only summary** view of a live week's (current or next) **definitive** meals that cannot be edited from this view. | US16 |
| FR-SUM-02 | ~~The summary shall display **who** made each meal definitive.~~ **Removed** — by G-79: promotion attribution is out of MVP scope. The candidate's own author (`FR-CAND-04`) is carried on the meal and remains visible in the summary; no separate record of who promoted it is stored or displayed. | — (removed by G-79; was US16) |
| FR-SUM-03 | Any attribution normally tied to a user (candidate authorship FR-CAND-04, library-recipe authorship FR-LIB-01, real-time change attribution FR-RT-02) shall display the **"unknown user"** placeholder when the originating account has since been removed (FR-AUTH-13). ~~rule edits FR-RULE-06~~ — **removed** by G-76: rules carry no author to resolve. ~~definitive-meal promotion FR-SUM-02~~ — **removed** by G-79: no promotion attribution is stored. | US4, US16 (see G-29; amended by G-76, G-79) |
| FR-ARCH-01 | The system shall persist **every past week's** menu and make it accessible at any time. | US25 |
| FR-ARCH-02 | When a week ends, its menu (candidates and definitives) shall be archived automatically and become read-only. A **snapshot of the shared shopping list** at rollover — taken **before** the rollover cleanup (FR-SHOP-09) — shall be stored with the archived week; the live list itself persists across rollovers. | US25 (gap, see resolution G-02; amended by G-52, G-53) |
| FR-ARCH-03 | Past weeks shall be retained **indefinitely**. A scheduled **cleanup job** shall move records **older than ~3 months** to **cheaper cold storage** (e.g. S3 Glacier). Cold records remain accessible, but retrieval may take minutes/hours; the UI shall show a "restoring…" state. | US25 (confirmed, see G-13, G-41) |
| FR-ARCH-04 | Archived weeks shall be browsable from a **reverse-chronological list/selector** of past weeks. | US25 (see G-27) |

---

## 8. General generation rules (shared)

| ID | Requirement | Source |
|----|-------------|--------|
| FR-RULE-01 | The system shall maintain a set of **general, predefined rules**, **shared among all users**, that apply to **every** week's generation. | US26 |
| FR-RULE-02 | Rules shall be displayed as a **list in their own dedicated section**. | US26 |
| FR-RULE-03 | Rules shall be editable **only via dropdowns** (a constrained, predefined value set; no free text). | US26 |
| FR-RULE-04 | Supported rule types shall include at minimum: number of meals per week per ingredient category (meat, fish, carbohydrates, legumes, ~~vegetarian~~ **vegetable**, …); pinning a specific **library meal** to a given day's lunch or dinner; and **disabling** generation for specific days. The ingredient-category list is a **fixed, predefined set** (application configuration, like the unit list of FR-SHOP-03) and is the **same set stored per recipe** in FR-LIB-03. **`vegetarian` replaced by `vegetable`** by G-82: every member of the set names a predominant *ingredient*, and a diet label overlaps every plant-based member by construction, leaving these counts unverifiable against the single value FR-LIB-03 stores. | US26 (see G-69, G-63; amended by G-82) |
| FR-RULE-05 | The system shall support a **per-week override** of the rules used by a single generation run (FR-AI-05) without altering the shared rules. | US13 |
| FR-RULE-06 | **Any user** may edit the shared rules; all edits are broadcast in real time. ~~all edits are attributed~~ — **attribution removed** by G-76: rule edits are not attributed in the MVP, so a rule stores no author. (No owner/governance role in the MVP.) | US26 (confirmed, see G-37; amended by G-76) |
| FR-RULE-07 | The system shall keep the rule set **consistent and satisfiable**: dropdown options shall prevent contradictory combinations (e.g. ingredient-category totals exceeding the slots available after disabled days, or pinning a meal on a disabled day). Deleting a library recipe referenced by a pin rule shall warn the user and remove the affected rule upon confirmation. | US18, US26 (see G-20) |

---

## 9. Shopping list

| ID | Requirement | Source |
|----|-------------|--------|
| FR-SHOP-01 | The system shall display a **single shared shopping list** covering the shopping horizon — the remainder of the current week plus the next week — showing every item's **name and quantity**. | US21 (resolves PEND-14, see G-52) |
| FR-SHOP-02 | Users shall be able to **add, edit (name and quantity), and remove** shopping-list items manually. | US22 |
| FR-SHOP-03 | The system shall provide a **button** that adds to the shopping list all the ingredients required by the in-scope meals (FR-SHOP-05), using a **fixed unit list** and aggregating only items with **matching name + unit** (no cross-unit conversion in the MVP). Name matching shall be **case-, accent- and leading/trailing-whitespace-insensitive**; no further fuzzy matching (e.g. singular/plural) in the MVP. | US23 (see G-39, G-52, G-56) |
| FR-SHOP-04 | Re-sync (FR-SHOP-06) shall **never delete any shopping-list item**, however it was created. The guarantee that manual items survive re-sync therefore holds by construction, and the MVP stores **no** auto/manual marker on an item. | US22, US23 (gap, see resolution G-04; amended by G-72) |
| FR-SHOP-05 | Auto-added ingredients shall derive **only from definitive meals**, in scope: the **current week from the current day onward** (Europe/Madrid, consistent with FR-AI-11) plus the **whole next week**. Candidates never contribute. | US8, US21, US23 (see G-04, G-52) |
| FR-SHOP-06 | The button (FR-SHOP-03) shall re-sync **on each press**, not continuously, and the operation shall be **purely additive**. Per normalized name + unit (FR-SHOP-03) it computes the **outstanding** quantity — the amount required by the in-scope definitive meals **minus** the amount already carried by **checked** items — and writes that outstanding amount to the matching **unchecked** item, adding one if none exists. **Checked items are never modified** (FR-SHOP-08): neither their quantity nor their state. When the outstanding amount is zero or less, nothing is added. **Nothing is ever removed.** Items no longer required by any in-scope definitive meal simply remain until a user deletes them (FR-SHOP-02) or rollover clears them once bought (FR-SHOP-09). The MVP stores **no** manual-override state: a user's edit to the quantity of an **unchecked** item that re-sync also derives may be overwritten by a later press. | US22, US23 (see G-21, G-52; amended by G-72, G-77) |
| FR-SHOP-07 | Shopping-list items shall be **checkable/uncheckable** to mark them as bought. | US24 (resolves PEND-10, see G-32) |
| FR-SHOP-08 | Checked items shall be displayed in a **separate section below** all unchecked items, shown **greyed out**; unchecking an item returns it to the unchecked section. Check state shall be **preserved** across re-sync (FR-SHOP-06) — re-sync shall **never modify a checked item at all**, neither unchecking it nor altering its quantity. A later increase in what the week requires reaches the user as a **new unchecked item** carrying the outstanding amount (FR-SHOP-06), not as a change to the item they already bought. ~~If a re-sync changes the quantity of a checked item, the item stays checked and shall be visually flagged as updated since it was checked.~~ — **Removed** by G-77: no updated-since-checked flag is stored or displayed. | US24 (see G-32; amended by G-77, supersedes G-44) |
| FR-SHOP-09 | At week rollover (FR-MENU-06), after the archive snapshot is taken (FR-ARCH-02), the shopping list shall **clear itself of every checked (bought) item**, unconditionally. **All unchecked items remain**, keeping their state — they represent shopping still pending. No per-item record of which live week requires an item is stored. | US23, US24 (see G-53; amended by G-73) |
| FR-SHOP-10 | The button's re-sync shall be **idempotent and serialized**: it recomputes the required-ingredient set **deterministically** from the in-scope definitive meals and applies it as an additive merge on normalized name + unit (FR-SHOP-06), so **repeated presses converge** — a second press with nothing else changed leaves the list exactly as the first left it. ~~never duplicated items~~ — **Removed** by G-77: a checked item and an unchecked item may deliberately share a normalized name + unit, since the outstanding amount is carried by a separate row rather than by modifying the purchase (FR-SHOP-08). **Serialization is unchanged and unresolved**: how concurrent presses are prevented from racing is deferred to the data-structure pass, not decided here. | US23 (see G-54; amended by G-72, G-77) |
| FR-SHOP-11 | ~~Grouping and marking likely-duplicate items.~~ **Removed** — re-sync merges on normalized name + unit, so an exact match is one row, never two. Items differing only by a form the normalization deliberately does not fold ("tomate" / "tomates", FR-SHOP-03) simply coexist; users resolve them with the ordinary edit and remove actions of FR-SHOP-02. | — (removed by G-74; was US22, US23, G-55) |

---

## 10. Collaboration & real-time

| ID | Requirement | Source |
|----|-------------|--------|
| FR-RT-01 | Changes made by one user to either live week's menu (candidates, definitive selections), to the **shared shopping list**, to the **rules**, or to the **shared library** shall be reflected to other users **in real time**. | US19 (see G-47) |
| FR-RT-02 | The collaboration model is fully shared: any user may view and edit candidates, the library, and the shared rules. Concurrent edits resolve **last-write-wins** (see resolution G-07). Author attribution applies to **candidates and library recipes**; ~~and the shared rules~~ — **rules are excluded** by G-78, since G-76 removed rule authorship: a rule edit is last-write-wins with no author recorded. | US10, US15, US18, US19 (amended by G-78) |
| FR-RT-03 | The UI shall **indicate loss of the real-time connection**, reconnect automatically, and re-synchronize state upon reconnection. | US19 (see G-22) |

---

## 11. Internationalization & UX

| ID | Requirement | Source |
|----|-------------|--------|
| FR-UX-01 | The entire UI shall be in **Castilian Spanish**. | US20 |
| FR-UX-02 | The application shall be a responsive website supporting the current major versions of desktop browsers (Windows/macOS/Linux) and mobile browsers (Android, iOS), including at minimum **Chrome, Firefox, Edge, Safari**, and Chromium-based browsers such as **Brave**. | US6 (resolves PEND-11, see G-33) |
| FR-UX-03 | **All** texts — including validation, error, and system messages — and date/number formats shall follow Castilian Spanish conventions (es-ES). | US20 (see G-23) |
| FR-UX-04 | Destructive actions (removing a recipe, candidate, shopping item, or rule; replacing or clearing a definitive meal; removing a user) shall require an **explicit confirmation**. | UX (see G-24) |
| FR-UX-05 | Views shall include **empty states** with guidance (empty library, day without candidates, empty shopping list) and **loading states** for slow operations. | UX (see G-25) |
| FR-UX-06 | The UI shall keep the **active week unambiguous** at all times: every week view, summary, and week-scoped action shall be labelled with the week (current / next) and its **Monday–Sunday date range**. | US7, US8 (see G-57) |
| FR-UX-07 | **Scope exclusion:** the MVP relies on **browser-default accessibility** only — no additional accessibility requirements (keyboard schemes, ARIA annotations, contrast targets) are in scope. | Stakeholder decision (resolves PEND-15, see G-62) |

---

## 12. Non-functional requirements (AWS final-project common requirements)

| ID | Requirement | Source |
|----|-------------|--------|
| NFR-ARCH-01 | The entire solution shall be deployed on **AWS** (or Kubernetes on AWS / EKS). | Common |
| NFR-IAC-01 | Infrastructure shall be defined in **Terraform**, except minimal bootstrap (account, initial IAM user, tfstate bucket). | Common |
| NFR-HA-01 | Production-traffic components shall run across **at least 2 availability zones**; loss of one AZ must not take the service down. | Common |
| NFR-BKP-01 | Every persistent datastore shall have **automated backups** (users, recipes, menus, past weeks, the shopping list and its archived snapshots, rules). | Common |
| NFR-CICD-01 | A functional CI/CD pipeline (GitHub Actions, CodePipeline, or equivalent) shall deploy the app on push to `main`. | Common |
| NFR-SEC-01 | IAM shall follow **least privilege**. | Common |
| NFR-SEC-02 | Secrets shall be kept **out of source code** (Secrets Manager / SSM Parameter Store / K8s secrets). | Common |
| NFR-SEC-03 | All internet-exposed traffic shall use **HTTPS**. | Common |
| NFR-SEC-04 | The login endpoint shall be protected against **brute force** (rate limiting and/or progressive lockout after repeated failures), with a generic failure message that does not reveal whether the username exists. | US2, US5 (see G-12) |
| NFR-OBS-01 | Logs shall be **centralized** (CloudWatch or equivalent). | Common |
| NFR-OBS-02 | At least **one active alarm** shall notify an email or channel. | Common |
| NFR-FIN-01 | All resources shall be tagged with `Project`, `Environment`, `Owner`. | Common |
| NFR-FIN-02 | **AWS Budgets** shall be configured with an overall monthly budget and cost alarm (overall figure set during implementation; the AI sub-cap is €50/month, see NFR-AI-01). | Common |
| NFR-DOC-01 | A public Git repo with coherent history and a README covering functional description, architecture diagram, **architecture-decision** section, reproducible deploy steps, monthly cost estimate, and teardown instructions. | Common |
| NFR-AI-01 | AI generation cost shall be capped at **€50/month for AI specifically**, enforced **globally for the whole deployment — not per user** — through **AWS cost-control tooling** (a dedicated AWS Budget with alarm, plus an enforcing path such as a Budget action, since Budgets alert but do not by themselves stop spend). The application stores and enforces **no per-user quota**. The system shall surface a friendly message in Castilian Spanish when AI generation is unavailable because the cap has been reached. | US12, US17 (see G-70, supersedes G-38) |

---

## 13. Traceability matrix (user story → requirements)

> **Removed requirements are dropped from this matrix, not struck through.** The
> requirement's own row above carries the strike-through and the reason; listing
> a dead id here would make the matrix disagree with it. Convention set by G-68
> (`FR-LIB-06` dropped from US17 and US18) and applied retroactively by **G-80**
> to `FR-SHOP-11` (US22, US23 — G-74) and `FR-SUM-02` (US16 — G-79), which had
> been struck in their own rows but left in the matrix.

| US | Covered by |
|----|------------|
| US1 | FR-AUTH-01, -03, -05, -06, -07, -12, -17, -18 |
| US2 | FR-AUTH-01, -02, -03, -04, -07, -16, -17, NFR-SEC-04 |
| US3 | FR-AUTH-01, -05, -11, -18 |
| US4 | FR-AUTH-12, -13, -14, -18, FR-SUM-03 |
| US5 | FR-AUTH-01, -02, -03, -04, -16, -17, NFR-SEC-04 |
| US6 | FR-UX-02 |
| US7 | FR-MENU-01, -02, -06, -08, FR-UX-06 |
| US8 | FR-MENU-01, -06, -07, -08, FR-SHOP-05, FR-UX-06 |
| US9 | FR-MENU-04, -05, FR-LIB-03 |
| US10 | FR-MENU-03, FR-CAND-01, -02, -03, -07, FR-LIB-05, FR-RT-02 |
| US11 | FR-CAND-06 |
| US12 | FR-AI-03, -04, -08, -09, -11, -12, -13, -14, NFR-AI-01 |
| US13 | FR-AI-04, -05, FR-RULE-05 |
| US14 | FR-AI-06 |
| US15 | FR-MENU-03, FR-CAND-04, -05, -08, FR-RT-02 |
| US16 | FR-SUM-01, -03 |
| US17 | FR-CAND-02, -03, FR-LIB-03, -05, FR-AI-01, -02, -08, -09, -10, -12, -13, -14, NFR-AI-01 |
| US18 | FR-CAND-03, -07, FR-LIB-01, -02, -04, -05, FR-RULE-07, FR-RT-02 |
| US19 | FR-AI-09, FR-RT-01, -02, -03 |
| US20 | FR-AI-07, FR-UX-01, -03 |
| US21 | FR-SHOP-01, -05 |
| US22 | FR-SHOP-02, -04, -06 |
| US23 | FR-SHOP-03, -04, -05, -06, -09, -10, FR-LIB-05 |
| US24 | FR-SHOP-07, -08, -09 |
| US25 | FR-ARCH-01, -02, -03, -04, FR-MENU-08 |
| US26 | FR-MENU-06, FR-AI-04, -11, FR-RULE-01, -02, -03, -04, -06, -07, FR-LIB-04 |
| US27 | FR-AUTH-04, -10, -11, -15 |
