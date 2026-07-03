# Gaps Pending Stakeholder Decision

> Companion to `requirements.md` and `gaps_and_resolutions.md`. This file
> tracks business decisions that could not be closed without stakeholder input.
> `PEND` IDs are **stable and never renumbered**, since they're cross-referenced
> from `requirements.md`'s Source column and from `gaps_and_resolutions.md`.
>
> **Status: all closed.** PEND-05, -07, -09, -10, -11, -12 and -13 were
> resolved on 2026-07-03 (three of them adding new user stories: US4, US8,
> US24). PEND-01, -02, -03, -04, -06 and -08 were confirmed as final by the
> stakeholder later the same day, exactly as their working assumption already
> documented them (G-36 to G-41). **PEND-14** was resolved and refined on
> **2026-07-04** (G-52, G-53). **PEND-15** was resolved on **2026-07-04**
> (G-62). This file is kept as a historical record.

## Resolved 2026-07-04

| ID | Question | Resolution | Reasoning | Requirements |
|----|----------|------------|-----------|---------------|
| PEND-14 | With two live weeks there are two shopping lists. Should there be a **combined view** for users who shop once for the rest of the current week and all of the next? | Yes, and further: a **single shared shopping list**. A **button** adds all ingredients for **definitive-only** meals in the current week (**only days forward from today**) and the next week; this replaces the two per-week lists and the automatic re-sync trigger. US23 rewritten accordingly. Refined same day: at week close, the list **clears itself of that week's bought items**, while items from the former next week remain. US24 extended accordingly. | G-52, G-53 | FR-SHOP-01, -03, -05, -06, -09, FR-MENU-06, FR-ARCH-02 |
| PEND-15 | What accessibility level should the app target (browser defaults / basic good practices / formal WCAG 2.1 AA)? | **Browser defaults only** — this is an MVP targeting basic core functionality. Recorded as an explicit scope-exclusion requirement so the absence of accessibility work reads as a decision, not an omission. | G-62 | FR-UX-07 |

## Resolved 2026-07-03 (added scope or a concrete new decision)

| ID | Question | Resolution | Reasoning | Requirements |
|----|----------|------------|-----------|---------------|
| PEND-05 | Password policy and session duration/expiry? | Left to industry-standard proposal (accepted): NIST SP 800-63B-aligned password policy; 12h idle / 30-day absolute session lifetime. | G-30, G-31 | FR-AUTH-15, FR-AUTH-16 |
| PEND-07 | Can users plan the **next** week before it becomes current? | Yes — added as a new story (US8) and a fully parallel "next week" live week with identical planning features. | G-28 | FR-MENU-01, -06, -07 and others (see requirements) |
| PEND-09 | Does "manage users" include **removing** an account, and what happens to its authored content? | Yes — new story (US4); removed users' content is kept, reattributed to a generic "unknown user". | G-29 | FR-AUTH-12, -13, -14, FR-SUM-03 |
| PEND-10 | Should shopping-list items be checkable (mark as bought)? | Yes — new story (US24); checked items move to a section below unchecked items, greyed out, and can be unchecked. | G-32 | FR-SHOP-07, -08 |
| PEND-11 | Which browsers/OS versions must be supported? | Confirmed: Android + PC + iOS, main browsers including Safari and Brave (Chromium-based) explicitly. | G-33 | FR-UX-02 |
| PEND-12 | Is library search/filter wanted as the shared library grows? | Yes — search by name, filter by cuisine/difficulty. | G-34 | FR-LIB-04 |
| PEND-13 | Expected number of users? | Confirmed: household/small-team scale (~2–10 users), as already assumed. | G-35 | (confirms NFR-AI-01, NFR-FIN-02 assumptions) |

## Resolved 2026-07-03 (confirmed the existing working assumption, no change)

| ID | Question | Working assumption confirmed as final | Reasoning | Requirements |
|----|----------|------------------------------------------|-----------|---------------|
| PEND-01 | What does "balanced and healthy" (US14) mean concretely? Are there dietary constraints, allergies, calorie targets? | Qualitative prompt instruction (vary protein sources) + quantitative balance via the general rules; output labelled non-medical. No medical/nutritional model in scope. | G-36 | FR-AI-06 |
| PEND-02 | Should shared-rule edits (US26) have any governance (owner, approval), or is free-for-all acceptable? | Any user edits; attributed and broadcast; no governance role in the MVP. | G-37 | FR-RULE-06 |
| PEND-03 | Final AI cost figures: is €50/month correct, and what per-user daily generation cap follows from it? | €50/month AI sub-budget confirmed. Exact per-user daily cap is an engineering calculation to be derived from provider pricing at implementation time, not a further business decision. | G-38 | NFR-AI-01 |
| PEND-04 | Which fixed unit list should the shopping list use (g, kg, ml, l, units, …)? Any cross-unit conversions ever wanted? | Fixed unit list, no cross-unit conversion in the MVP, confirmed as the approach; the literal unit enumeration is an implementation detail. | G-39 | FR-SHOP-03 |
| PEND-06 | Is one bootstrap admin enough, and is IaC re-seeding an acceptable recovery path? | One bootstrap admin; multiple supported; recovery via re-seeding the IaC-managed secret. | G-40 | FR-AUTH-07, -08 |
| PEND-08 | Retention policy: is "indefinite, cold storage after ~3 months" right? Is minutes-to-hours retrieval for old weeks acceptable? | Indefinite retention; move to cold storage (e.g. Glacier) after ~3 months; "restoring…" UI state. | G-41 | FR-ARCH-03 |
