# gga review findings — fix report

Scope: fix exactly the three findings below, blocking a human commit. No
feature work, no `feature_list.json` change, nothing else touched.

## Finding 1 — stale citation in `frontend/src/tokens/colors.js:4-5`

**Problem**: the header comment argued against a claim
(`docs/frontend_prototype.md` "the 13 colour tokens") that the document no
longer makes — it was corrected to 18 in both cited places (§2.4 line 140,
§6.1 line 277; re-verified before editing). The stale parenthetical read as
disputing a live source-of-truth document.

**Fix**: removed the parenthetical dispute, kept the "18 custom properties /
lifted verbatim / §2.4 + §6.1" statement.

```diff
 /**
  * Colour tokens, lifted verbatim from the 18 CSS custom properties on
  * prototypes/wireframe/Sobremesa.dc.html:33 (see docs/frontend_prototype.md
- * section 2.4 and section 6.1 — "the 13 colour tokens" is that document's own
- * count; the line actually carries 18, all reproduced here unmodified).
+ * section 2.4 and section 6.1), all reproduced here unmodified.
  *
```

The 18 hex values in the file body were not touched.

## Finding 2 — timezone-dependent assertion in `frontend/tests/locale.test.js`

**Problem**: `new Date(Date.UTC(2026, 0, 15, 12))` fixes a UTC instant, then
`formatDate()` (no `timeZone` option — `frontend/src/locale.js:9`) renders it
in the runner's *local* zone. At offsets UTC+13 or UTC+14 (e.g.
`Pacific/Auckland` in DST, `Pacific/Kiritimati`), that instant lands on the
16th, and `toContain('15')` fails.

**Fix chosen**: build the fixture from **local** Date components instead of
`Date.UTC`:

```diff
-    const date = new Date(Date.UTC(2026, 0, 15, 12));
+    const date = new Date(2026, 0, 15, 12);
```

**Why this option, and not a `timeZone` pin in `vite.config.js`**:
`new Date(y, m, d, h)` and `Intl.DateTimeFormat(LOCALE).format()` (no
`timeZone` option) both read the *same* single "process local zone" value.
Building the fixture from local components means construction and formatting
are anchored to the same zone by construction — there is no UTC↔local
conversion in between for a day-boundary case to trip on, regardless of what
that zone actually is. This is a spec-level invariant, not a lucky offset
choice, so it holds at every real UTC offset (-12:00 to +14:00 — verified
below). It also leaves `frontend/src/locale.js` — the production code —
completely unchanged, per the instruction to prefer options that don't alter
`formatDate`'s behaviour. Pinning `TZ` in `vite.config.js` was rejected
because it would only prove the assertion passes under one hard-coded zone
chosen by us, not under an arbitrary runner zone, and it would encode a
production-adjacent config change to paper over a test-fixture bug.

**Mandatory proof — hostile timezone**

The three requested commands, run verbatim from `frontend/`:

```
$ TZ=Pacific/Kiritimati npx --no -- vitest run
 Test Files  3 passed (3)
      Tests  5 passed (5)

$ TZ=Europe/Madrid npx --no -- vitest run
 Test Files  3 passed (3)
      Tests  5 passed (5)

$ TZ=UTC npx --no -- vitest run
 Test Files  3 passed (3)
      Tests  5 passed (5)
```

All three green — but this is **not sufficient evidence by itself** on this
machine, see below.

**`TZ` is not honoured for named IANA zones on this Windows/Git-Bash setup**
(explicitly flagged per the instructions, not silently skipped). Diagnosis:

```
$ TZ=UTC sh -c 'node -e "console.log(JSON.stringify(process.env.TZ))"'
"UTC"
$ TZ=Europe/London sh -c 'node -e "console.log(JSON.stringify(process.env.TZ))"'
undefined
$ TZ=Pacific/Kiritimati sh -c 'node -e "console.log(JSON.stringify(process.env.TZ))"'
undefined
```

Any `TZ` value containing a `/` (i.e. every real IANA zone name except
`UTC`) is silently dropped before it reaches `node.exe`, even though the
shell (`env`, `sh -c 'echo $TZ'`) has it correctly. Reproduced with
`export`, inline assignment, `env TZ=... node`, `MSYS_NO_PATHCONV=1`, and
`MSYS2_ENV_CONV_EXCL=TZ` — none restore it. So the three commands above
prove the suite is green, but only the `TZ=UTC` run actually changed the
process's resolved zone (confirmed: `Intl.DateTimeFormat().resolvedOptions().timeZone`
stayed `Europe/Madrid` for the `Pacific/Kiritimati` and `Europe/Madrid` runs
alike). `TZ=Pacific/Kiritimati` did **not** exercise a different zone here.

**Alternative determinism proof** (since the hostile zone can't actually be
set on this machine): the fix's correctness is a *spec-level invariant* —
`new Date(y,m,d,h)` and `Intl.DateTimeFormat(locale).format()` with no
`timeZone` option both resolve against the exact same "local zone" value
within one process. Verified by simulating every real-world UTC offset
(-12:00 .. +14:00, the full range that exists on Earth) and checking the
round trip never crosses a day boundary:

```
UTC-12h    -> day 15 PASS
UTC-11h    -> day 15 PASS
UTC+0h     -> day 15 PASS
UTC+1h     -> day 15 PASS
UTC+2h     -> day 15 PASS
UTC+12h    -> day 15 PASS
UTC+13h    -> day 15 PASS
UTC+14h    -> day 15 PASS
ALL PASS
```

And confirming the *old* fixture (`Date.UTC` construction, local-zone
formatting) genuinely breaks under the same method — i.e. this was a real
bug, not a false positive:

```
UTC-12h    -> day 15 PASS
UTC+0h     -> day 15 PASS
UTC+2h     -> day 15 PASS
UTC+13h    -> day 16 FAIL (old test would break here)
UTC+14h    -> day 16 FAIL (old test would break here)
```

This confirms both that the finding was real (old fixture fails at UTC+13
and UTC+14, exactly the Auckland-DST / Kiritimati cases named in the
finding) and that the fix removes the failure at every possible offset, not
just the offsets this machine happens to be able to reach via `TZ`.

## Finding 3 — inert ignore patterns in `frontend/eslint.config.js:9`

**Problem**: flat-config `ignores` match paths relative to the config's base
path, which never start with `../`. `'../backend/**'` and
`'../prototypes/**'` never match anything — dead code that reads as a
boundary the config does not actually enforce (the boundary is real, but it
comes from ESLint being invoked with cwd `frontend/`, not from this list).

**Fix**: removed the two inert patterns, kept `'dist/**'` and
`'node_modules/**'` (both live matches), and rewrote the comment to name the
actual mechanism (cwd-scoping) instead of implying the ignore list does it.

```diff
-// Flat config, scoped to this toolchain root only. `frontend/` never reads
-// `backend/` and never reaches `prototypes/` (docs/architecture.md section 3).
+// Flat config, scoped to this toolchain root only. ESLint is invoked with
+// cwd `frontend/`, so it cannot walk outward and reach `backend/` or
+// `prototypes/` (docs/architecture.md section 3) — that isolation comes from
+// how it is run, not from the ignores list below.
 export default [
   {
-    ignores: ['dist/**', 'node_modules/**', '../backend/**', '../prototypes/**'],
+    ignores: ['dist/**', 'node_modules/**'],
   },
```

`frontend/.prettierignore` was left untouched (already correctly has no
`../prototypes/**` entry, per the same reasoning — not part of this task's
scope regardless).

**Reach check** — confirms removing the two dead entries did not widen what
ESLint actually lints (still exactly the files under `frontend/`, nothing
under `backend/` or `prototypes/`):

```
$ npx --no -- eslint . --format json   # 16 files, all under frontend/
frontend/eslint.config.js
frontend/src/PlaceholderView.jsx
frontend/src/locale.js
frontend/src/main.jsx
frontend/src/messages/es-ES.js
frontend/src/messages/index.js
frontend/src/tokens/breakpoints.js
frontend/src/tokens/colors.js
frontend/src/tokens/index.js
frontend/src/tokens/spacing.js
frontend/src/tokens/typography.js
frontend/tests/PlaceholderView.test.jsx
frontend/tests/htmlMessages.test.js
frontend/tests/locale.test.js
frontend/vite-plugins/htmlMessages.js
frontend/vite.config.js
```

## Verification

```
$ cd frontend && npx --no -- eslint .
(exit 0, no output)

$ cd frontend && npx --no -- prettier --check .
Checking formatting...
All matched files use Prettier code style!
(exit 0)
```

```
$ ./init.sh
...
── 5. Quality gates ────────────────────────────────────
[OK]    ruff format
[OK]    ruff check
[OK]    mypy
1 passed in 0.02s
[OK]    pytest (unit + contract, no AWS)
[OK]    prettier --check
[OK]    eslint
[OK]    vitest

── 6. Summary ──────────────────────────────────────────
[OK]    Environment ready. You can start working.
(exit 0)
```

## Files changed

- `frontend/src/tokens/colors.js`
- `frontend/tests/locale.test.js`
- `frontend/eslint.config.js`

Nothing else was touched. No dependency added. No `git` write command run.
