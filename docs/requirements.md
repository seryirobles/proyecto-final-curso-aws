# Requirements Specification — Collaborative Weekly Meal Planner

> Derived from `app_user_stories.md` (functional team) and the common project
> requirements in `cloud_aws_enunciados-proyecto-final/` (AWS final project,
> "libre" option). Each requirement is traceable to the originating user story
> (`US#`). Decisions taken to fill ambiguities are documented in
> `gaps_and_resolutions.md`; open business decisions are listed in
> `gaps_pending_stakeholders.md`.

## 1. Product summary

A web application (desktop + mobile) where a fixed set of **users**, created and
managed by an **admin**, collaboratively plan the meals of the current week
(Monday–Sunday, lunch and dinner). Users propose candidate meals per day, pick a
definitive meal per slot, maintain a shared recipe library, generate recipes and
whole-week plans with AI under shared rules, build a shopping list, and consult an
archive of past weeks — all in Castilian Spanish, with changes reflected in real
time between users.

---

## 2. Roles and access control

| ID | Requirement | Source |
|----|-------------|--------|
| FR-AUTH-01 | The system shall support exactly two roles: **Admin** (user management) and **User** (meal planning). | US1–US3 |
| FR-AUTH-02 | Authentication shall be by **username + password** for both roles. | US2, US3 |
| FR-AUTH-03 | The system shall **not** offer public self-registration for any role. Users are created only by an admin. | US1, US2, US3 |
| FR-AUTH-04 | Neither admins nor users shall be able to change **their own** password through the application. | US2, US3 |
| FR-AUTH-05 | The Admin shall have an **exclusive view** restricted to user management: create users, change usernames, and change/reset user passwords. The admin shall have **no access** to any meal-planning feature. | US1 |
| FR-AUTH-06 | Users shall have access to all meal-planning features but **no** access to the admin/user-management view. | US1 |
| FR-AUTH-07 | Exactly **one** Admin account shall be provisioned at deployment time (bootstrap). The system shall **support multiple admins** so they can reset each other, but only one is created initially. | US1, US2, PEND-06 (see G-01) |
| FR-AUTH-08 | Admin account recovery shall be possible by **re-seeding** the bootstrap admin from its IaC-managed secret. | PEND-06 (see G-08) |
| FR-AUTH-09 | The application shall enforce HTTPS-only access and authenticated sessions; users shall be able to log out. | NFR/security |

---

## 3. Week menu — structure and viewing

| ID | Requirement | Source |
|----|-------------|--------|
| FR-MENU-01 | The system shall present the **current week's** menu split into 7 days (Monday→Sunday) and, per day, two meal slots: **lunch** and **dinner**. | US5 |
| FR-MENU-02 | "Current week" shall be computed as the ISO week (Monday–Sunday) in the **Europe/Madrid** timezone. | US5 (gap, see resolution G-02) |
| FR-MENU-03 | Each meal slot holds a list of **candidate** meals and at most one **definitive** meal. | US7, US12 |
| FR-MENU-04 | Clicking a meal shall open its detailed recipe: **ingredients (with quantities), tools, and procedure**. | US6 |

---

## 4. Candidates and recipe authoring

| ID | Requirement | Source |
|----|-------------|--------|
| FR-CAND-01 | A user shall be able to **add, edit, or remove** candidate meals for any day/slot, individually. | US7 |
| FR-CAND-02 | When adding/editing a candidate, the user shall choose one of three authoring methods: (a) pick an existing recipe from the **library**, (b) write a **new recipe from scratch**, or (c) **generate one with AI**. | US7, US14 |
| FR-CAND-03 | Creating/editing a recipe in the **library** shall reuse the same authoring flows as candidate authoring — specifically **writing from scratch** and **generating with AI** (FR-AI-01/-02, same UI and specification options: ingredients, tools, cuisine, difficulty, or a library recipe as reference). The "pick an existing library recipe" method does not apply here, since the target is the library itself. | US7, US14, US15 |
| FR-CAND-04 | A user shall be able to view candidate meals for a day regardless of whether they were created by themselves or by other users. | US12 |
| FR-CAND-05 | A user shall be able to **promote a candidate to definitive** for its slot, replacing any previous definitive. | US12 |
| FR-CAND-06 | A meal shown in the week menu shall be **addable to the library** for reuse in other weeks. | US8 |
| FR-CAND-07 | A recipe added to a menu shall store a **snapshot** of the recipe content, so later library edits/deletes do not silently mutate existing or past menus. | US7, US15 (gap, see resolution G-05) |

---

## 5. Recipe library

| ID | Requirement | Source |
|----|-------------|--------|
| FR-LIB-01 | Users shall see **all** recipes in the shared library, regardless of author. | US15 |
| FR-LIB-02 | Users shall be able to **add, edit, and remove** library recipes, using the same write-from-scratch and AI-generation authoring flows as candidate authoring (see FR-CAND-03). | US15 |
| FR-LIB-03 | A library recipe shall store: name, ingredients with quantities, tools, procedure, and the AI-relevant attributes cuisine and difficulty when available. | US6, US14 |

---

## 6. AI generation

| ID | Requirement | Source |
|----|-------------|--------|
| FR-AI-01 | The system shall generate a **single recipe** with AI from user inputs: ingredients, tools, cuisine, and difficulty. | US14 |
| FR-AI-02 | The system shall alternatively generate a **single recipe** based on a chosen **library recipe as reference** plus extra user specifications. | US14 |
| FR-AI-03 | The system shall generate a **whole week's plan** with AI, in one of three modes: (a) only library meals, (b) only newly AI-generated meals, or (c) a **mix**; all generated meals shall be added to their respective days/slots **as candidates**. | US9 |
| FR-AI-04 | Whole-week generation shall honor the active **general rules** (Section 8). | US9, US10, US22 |
| FR-AI-05 | Before whole-week generation, the system shall show a **confirmation prompt** displaying the current general rules and offering to **edit them only for this week's generation** (a per-week override that does not modify the shared rules). | US10 (gap, see resolution G-06) |
| FR-AI-06 | The AI prompt shall explicitly instruct the model to produce **healthy, balanced** menus that **vary protein sources**. Quantitative balance (how many meals per ingredient category) is enforced through the **general rules** (Section 8), not the prompt. Output is labelled **non-medical**. | US11, PEND-01 |
| FR-AI-07 | AI output (recipe text, ingredients, procedure) shall be produced in **Castilian Spanish**. | US17 |
| FR-AI-08 | AI generation shall be **idempotent**: submitting the same generation request (same week, slot(s), and effective rules) more than once — whether by retry, double-click, or network re-send — shall **not** produce duplicate candidates nor duplicate AI invocations/charges. Idempotency shall be enforced via a generation key (e.g. a hash of the request) and conditional writes. | US9, US14 |
| FR-AI-09 | AI generation shall support **concurrency**: multiple users (and the per-slot tasks of a single whole-week generation) may run AI generations simultaneously without lost updates, double-writes, or corrupting each other's candidates. Per-slot results shall be written independently and the failure of one shall not abort the others. | US9, US14, US16 |

---

## 7. Weekly summary, archive, and attribution

| ID | Requirement | Source |
|----|-------------|--------|
| FR-SUM-01 | The system shall provide a **read-only summary** view of the week's **definitive** meals that cannot be edited from this view. | US13 |
| FR-SUM-02 | The summary shall display **who** made each meal definitive. | US13 |
| FR-ARCH-01 | The system shall persist **every past week's** menu and make it accessible at any time. | US21 |
| FR-ARCH-02 | When a week ends, its menu (candidates, definitives, shopping list) shall be archived automatically and become read-only. | US21 (gap, see resolution G-02) |
| FR-ARCH-03 | Past weeks shall be retained **indefinitely**. A scheduled **cleanup job** shall move records **older than ~3 months** to **cheaper cold storage** (e.g. S3 Glacier). Cold records remain accessible, but retrieval may take minutes/hours; the UI shall show a "restoring…" state. | US21, PEND-08 (see G-13) |

---

## 8. General generation rules (shared)

| ID | Requirement | Source |
|----|-------------|--------|
| FR-RULE-01 | The system shall maintain a set of **general, predefined rules**, **shared among all users**, that apply to **every** week's generation. | US22 |
| FR-RULE-02 | Rules shall be displayed as a **list in their own dedicated section**. | US22 |
| FR-RULE-03 | Rules shall be editable **only via dropdowns** (a constrained, predefined value set; no free text). | US22 |
| FR-RULE-04 | Supported rule types shall include at minimum: number of meals per week per ingredient category (meat, fish, carbohydrates, legumes, vegetarian, …); pinning a specific **library meal** to a given day's lunch or dinner; and **disabling** generation for specific days. | US22 |
| FR-RULE-05 | The system shall support a **per-week override** of the rules used by a single generation run (FR-AI-05) without altering the shared rules. | US10 |
| FR-RULE-06 | **Any user** may edit the shared rules; all edits are attributed and broadcast in real time. (No owner/governance role in the MVP.) | US22, PEND-02 |

---

## 9. Shopping list

| ID | Requirement | Source |
|----|-------------|--------|
| FR-SHOP-01 | The system shall display a shopping list for the week showing every item's **name and quantity**. | US18 |
| FR-SHOP-02 | Users shall be able to **add, edit (name and quantity), and remove** shopping-list items manually. | US19 |
| FR-SHOP-03 | The system shall **automatically add** to the shopping list the ingredients required by the current week's meals, using a **fixed unit list** and aggregating only items with **matching name + unit** (no cross-unit conversion in the MVP). | US20, PEND-04 |
| FR-SHOP-04 | Auto-generated items shall be distinguishable from manually-added items; re-syncing auto items shall **not** delete manual items. | US19, US20 (gap, see resolution G-04) |
| FR-SHOP-05 | The shopping list shall be derived from the week's **definitive** meals. | US18, US20 (gap, see resolution G-04) |

---

## 10. Collaboration & real-time

| ID | Requirement | Source |
|----|-------------|--------|
| FR-RT-01 | Changes made by one user to the week menu (candidates, definitive selection, shopping list, rules) shall be reflected to other users **in real time**. | US16 |
| FR-RT-02 | The collaboration model is fully shared: any user may view and edit candidates, the library, and the shared rules. Concurrent edits resolve **last-write-wins** with author attribution (see resolution G-07). | US7, US12, US15, US16 |

---

## 11. Internationalization & UX

| ID | Requirement | Source |
|----|-------------|--------|
| FR-UX-01 | The entire UI shall be in **Castilian Spanish**. | US17 |
| FR-UX-02 | The application shall be a **responsive website** usable on both desktop and mobile browsers. | US4 |

---

## 12. Non-functional requirements (AWS final-project common requirements)

| ID | Requirement | Source |
|----|-------------|--------|
| NFR-ARCH-01 | The entire solution shall be deployed on **AWS** (or Kubernetes on AWS / EKS). | Common |
| NFR-IAC-01 | Infrastructure shall be defined in **Terraform**, except minimal bootstrap (account, initial IAM user, tfstate bucket). | Common |
| NFR-HA-01 | Production-traffic components shall run across **at least 2 availability zones**; loss of one AZ must not take the service down. | Common |
| NFR-BKP-01 | Every persistent datastore shall have **automated backups** (users, recipes, menus, past weeks, shopping lists, rules). | Common |
| NFR-CICD-01 | A functional CI/CD pipeline (GitHub Actions, CodePipeline, or equivalent) shall deploy the app on push to `main`. | Common |
| NFR-SEC-01 | IAM shall follow **least privilege**. | Common |
| NFR-SEC-02 | Secrets shall be kept **out of source code** (Secrets Manager / SSM Parameter Store / K8s secrets). | Common |
| NFR-SEC-03 | All internet-exposed traffic shall use **HTTPS**. | Common |
| NFR-OBS-01 | Logs shall be **centralized** (CloudWatch or equivalent). | Common |
| NFR-OBS-02 | At least **one active alarm** shall notify an email or channel. | Common |
| NFR-FIN-01 | All resources shall be tagged with `Project`, `Environment`, `Owner`. | Common |
| NFR-FIN-02 | **AWS Budgets** shall be configured with an overall monthly budget and cost alarm (overall figure set during implementation; the AI sub-cap is €50/month, see NFR-AI-01). | Common |
| NFR-DOC-01 | A public Git repo with coherent history and a README covering functional description, architecture diagram, **architecture-decision** section, reproducible deploy steps, monthly cost estimate, and teardown instructions. | Common |
| NFR-AI-01 | AI generation cost shall be capped at **€50/month for AI specifically** (a dedicated AWS Budget/alarm), enforced via a **per-user daily generation cap**; the system shall surface a friendly message when a limit is exceeded. | US9, US14, PEND-03 |

---

## 13. Traceability matrix (user story → requirements)

| US | Covered by |
|----|------------|
| US1 | FR-AUTH-01, -05, -07 |
| US2 | FR-AUTH-02, -03, -04, -07 |
| US3 | FR-AUTH-02, -03, -04, -06 |
| US4 | FR-UX-02 |
| US5 | FR-MENU-01, -02 |
| US6 | FR-MENU-04, FR-LIB-03 |
| US7 | FR-CAND-01, -02, -03, -07 |
| US8 | FR-CAND-06 |
| US9 | FR-AI-03, -04, -08, -09, NFR-AI-01 |
| US10 | FR-AI-05, FR-RULE-05 |
| US11 | FR-AI-06 |
| US12 | FR-CAND-04, -05, FR-MENU-03 |
| US13 | FR-SUM-01, -02 |
| US14 | FR-AI-01, -02, -08, -09, FR-LIB-03 |
| US15 | FR-LIB-01, -02, FR-CAND-03, -07 |
| US16 | FR-RT-01, -02, FR-AI-09 |
| US17 | FR-UX-01, FR-AI-07 |
| US18 | FR-SHOP-01, -05 |
| US19 | FR-SHOP-02, -04 |
| US20 | FR-SHOP-03, -04, -05 |
| US21 | FR-ARCH-01, -02 |
| US22 | FR-RULE-01..05 |
