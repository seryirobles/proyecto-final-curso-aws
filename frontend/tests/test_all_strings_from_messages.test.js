// R15, design.md section 9 (spot-check, mirrors the same mechanical-scan
// idea as test_no_self_password_change.test.js). See
// progress/impl_frontend_spa.md's "T62" sections for the scan's design.

import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const TESTS_ROOT = dirname(fileURLToPath(import.meta.url));
const COMPONENTS_DIR = join(TESTS_ROOT, '..', 'src', 'components');

const LINE_COMMENT = /\/\/.*$/gm;
const BLOCK_COMMENT = /\/\*[\s\S]*?\*\//g;
const IMPORT_LINE = /^\s*import\b.*$/gm;
const STRING_LITERAL = /"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'/g;
const TEMPLATE_LITERAL = /`(?:\\.|\$\{[^{}]*\}|[^`\\])*`/g;
const HAS_CONTENT = /[\p{L}\p{N}]/u;
const IDENTIFIER = /^[A-Za-z_$][\w$]*$/;

// Prop/attribute names that never carry rendered copy (Finding 1, fix round
// 2) - structural/technical plumbing. Anything NOT on this list, quoted and
// letter-bearing, is a hardcoded prop-text pass-through and gets flagged.
const SAFE_ATTR_NAMES = new Set([
  'type',
  'className',
  'id',
  'key',
  'htmlFor',
  'name',
  'href',
  'src',
  'data-testid',
  'role',
  'designation',
  'value',
  // SVG icon geometry (T82/T83, design.md 10.6) - numeric/keyword, never copy.
  'width',
  'height',
  'viewBox',
  'fill',
  'stroke',
  'strokeWidth',
  'strokeLinecap',
  'strokeLinejoin',
  'd',
  // SearchIcon's <circle> (T86, design.md 10.6) - same class as the above.
  'cx',
  'cy',
  'r',
  // Comensales numeric stepper (issue servings-and-time-inputs-not-numeric)
  // - an HTML step increment, never copy.
  'step',
  // Tiempo estimado's minute bounds (issue tiempo-estimado-numeric-minutes,
  // G-90) - HTML range limits, never copy.
  'min',
  'max',
  // Browser form hints (frontend_ux_phase1 R16, R20) - never copy.
  'autoComplete',
  'autoCapitalize',
]);
const ATTR_ASSIGNMENT = /([A-Za-z][\w-]*)\s*=\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g;
// A string literal counts as a rendered branch/fallback only right after one
// of these operators (or at the very start of its expression container) —
// excludes comparison operands like `activeView === 'week'`.
const RENDER_POSITION_SUFFIX = /(?:^|[?:]|\|\||\?\?|&&|=>)$/;
const COMPARISON_SUFFIX = /[!=]==?$/;

// Scans quoted (non-`{}`) attribute values; strips every one (technical
// plumbing is never rendered text) but flags a non-allowlisted, letter-
// bearing one as a hardcoded prop-text pass-through (Finding 1).
function scanAttributeStrings(text, violations) {
  return text.replace(ATTR_ASSIGNMENT, (_full, name, quoted) => {
    if (!SAFE_ATTR_NAMES.has(name) && HAS_CONTENT.test(quoted)) {
      violations.push(quoted);
    }
    return name;
  });
}

// True if a template literal (Finding 2) has a hardcoded text segment with
// letters/digits outside its `${...}` interpolations, e.g. `` `Semana ${n}` ``.
function hasStaticContent(templateLiteral) {
  return HAS_CONTENT.test(templateLiteral.replace(/\$\{[^{}]*\}/g, ''));
}

// Flags a string/template literal in `text` only when it sits in a
// rendering position (see RENDER_POSITION_SUFFIX) - shared by scanRegion's
// `{...}` spans and by a resolved const initializer (Finding 3).
function findRenderPositionLiterals(text, violations) {
  for (const literalMatch of text.matchAll(STRING_LITERAL)) {
    const before = text.slice(0, literalMatch.index).trimEnd();
    if (COMPARISON_SUFFIX.test(before)) continue;
    if (RENDER_POSITION_SUFFIX.test(before) && HAS_CONTENT.test(literalMatch[0])) {
      violations.push(literalMatch[0]);
    }
  }
  for (const templateMatch of text.matchAll(TEMPLATE_LITERAL)) {
    const before = text.slice(0, templateMatch.index).trimEnd();
    if (COMPARISON_SUFFIX.test(before)) continue;
    if (RENDER_POSITION_SUFFIX.test(before) && hasStaticContent(templateMatch[0])) {
      violations.push(templateMatch[0]);
    }
  }
}

// Maps every top-level `const NAME = <expr>;` in a file to its initializer
// text (Finding 3: a WeekLabel.jsx-style const computed above `return`,
// then referenced bare as `{name}` inside it).
function collectConstInitializers(source) {
  const map = new Map();
  const re = /\bconst\s+([A-Za-z_$][\w$]*)\s*=\s*/g;
  let match;
  while ((match = re.exec(source))) {
    let depth = 0;
    let j = re.lastIndex;
    for (; j < source.length; j++) {
      const c = source[j];
      if (c === '(' || c === '{' || c === '[') depth++;
      else if (c === ')' || c === '}' || c === ']') depth--;
      else if (c === ';' && depth <= 0) break;
    }
    map.set(match[1], source.slice(re.lastIndex, j));
    re.lastIndex = j;
  }
  return map;
}

// Attribute-value shapes that never carry copy: an object literal (style/
// config props) or a function/arrow-function body (event handlers) - never
// a copy-passing shape, unlike a bare/ternary string (Finding 1, round 3).
const NON_COPY_ATTR_VALUE = /^\{|^\(?[\w,\s]*\)?\s*=>|^function\b/;
const EVENT_HANDLER_ATTR = /^on[A-Z]/;

// Strips `attr={...}` so the tag scan below stays clean; see
// progress/impl_frontend_spa.md — "T62 — Fix round 3" for why.
function stripAttributeExpressions(text, violations) {
  let out = '';
  let i = 0;
  while (i < text.length) {
    if (text[i] === '=' && text[i + 1] === '{') {
      const nameMatch = /([A-Za-z][\w-]*)\s*$/.exec(out);
      const name = nameMatch ? nameMatch[1] : '';
      out += '=';
      let depth = 1;
      let j = i + 2;
      while (j < text.length && depth > 0) {
        if (text[j] === '{') depth++;
        else if (text[j] === '}') depth--;
        j++;
      }
      const inner = text.slice(i + 2, j - 1);
      if (
        !SAFE_ATTR_NAMES.has(name) &&
        name !== 'style' &&
        !EVENT_HANDLER_ATTR.test(name) &&
        !NON_COPY_ATTR_VALUE.test(inner.trim())
      ) {
        findRenderPositionLiterals(inner, violations);
      }
      i = j;
    } else {
      out += text[i];
      i++;
    }
  }
  return out;
}

// Splits `text` into its top-level (balanced) `{...}` spans - JSX children
// expression containers - and the surrounding markup/bare-text.
function splitTopLevelBraces(text) {
  const outsideParts = [];
  const insideSpans = [];
  let buf = '';
  let i = 0;
  while (i < text.length) {
    if (text[i] === '{') {
      outsideParts.push(buf);
      buf = '';
      let depth = 1;
      let j = i + 1;
      while (j < text.length && depth > 0) {
        if (text[j] === '{') depth++;
        else if (text[j] === '}') depth--;
        j++;
      }
      insideSpans.push(text.slice(i + 1, j - 1));
      i = j;
    } else {
      buf += text[i];
      i++;
    }
  }
  outsideParts.push(buf);
  return { outsideText: outsideParts.join(''), insideSpans };
}

// A real JSX tag, e.g. `<p>`, `</p>`, `<Foo bar="baz" />` - used to find
// bare text between actual SIBLING tags, never between a `.length > 0`
// comparison and some later tag (the naive `>...<` scan's false positive).
const TAG = /<\/?[A-Za-z][\w.]*(?:\s(?:[^<>"']|"[^"]*"|'[^']*')*)?\/?>/g;

// A gap between two sibling tags that also carries ternary/method-call JS
// syntax (an operator alongside a paren), e.g. `) : (` or `.map((x) => (`
// joining two *different* branches - not two siblings sharing a text node.
const JS_SYNTAX_GAP = /[?:]|=>/;

// Recursively scans JSX-mixed text for a rendering-position string/template
// literal (inline or via a resolved const, Finding 3) inside `{...}`, and
// bare JSX text between sibling tags - all outside MESSAGES.*, R15.
function scanRegion(text, violations, constInitializers = new Map()) {
  const { outsideText, insideSpans } = splitTopLevelBraces(text);

  const tags = [...outsideText.matchAll(TAG)];
  for (let i = 0; i + 1 < tags.length; i++) {
    const gap = outsideText.slice(tags[i].index + tags[i][0].length, tags[i + 1].index);
    const bareText = gap.trim();
    const looksLikeJs = /[()]/.test(bareText) && JS_SYNTAX_GAP.test(bareText);
    if (bareText && !looksLikeJs && HAS_CONTENT.test(bareText)) {
      violations.push(bareText);
    }
  }

  for (const span of insideSpans) {
    findRenderPositionLiterals(span, violations);
    const trimmed = span.trim();
    if (IDENTIFIER.test(trimmed) && constInitializers.has(trimmed)) {
      findRenderPositionLiterals(constInitializers.get(trimmed), violations);
    }
    scanRegion(span, violations, constInitializers);
  }
}

// True if `text` (trimmed) opens with `<...` or `(<...` - a component only
// ever renders JSX this way; excludes a helper like `return { ... };`
// (a plain style-object literal, not markup) from being scanned as JSX.
function looksLikeJsxReturn(text) {
  let i = 0;
  while (/\s/.test(text[i])) i++;
  if (text[i] === '<') return true;
  if (text[i] === '(') {
    let j = i + 1;
    while (/\s/.test(text[j])) j++;
    return text[j] === '<';
  }
  return false;
}

// Extracts every `return <expr>;` statement's JSX `<expr>` text (balanced
// over `(`/`{`/`[`) - the only place a component renders markup, so it is
// the only text this guard needs to inspect.
function extractReturnBlocks(source) {
  const blocks = [];
  const re = /\breturn\b/g;
  while (re.exec(source)) {
    let i = re.lastIndex;
    while (/\s/.test(source[i])) i++;
    let depth = 0;
    let j = i;
    for (; j < source.length; j++) {
      const c = source[j];
      if (c === '(' || c === '{' || c === '[') depth++;
      else if (c === ')' || c === '}' || c === ']') depth--;
      else if (c === ';' && depth <= 0) break;
    }
    const block = source.slice(i, j);
    if (looksLikeJsxReturn(block)) blocks.push(block);
  }
  return blocks;
}

function jsxFiles(dir) {
  return readdirSync(dir, { recursive: true })
    .filter((entry) => entry.endsWith('.jsx'))
    .map((entry) => join(dir, entry));
}

function strayLiterals(path) {
  const stripped = readFileSync(path, 'utf8')
    .replace(BLOCK_COMMENT, '')
    .replace(LINE_COMMENT, '')
    .replace(IMPORT_LINE, '');

  const violations = [];
  const constInitializers = collectConstInitializers(stripped);
  for (const block of extractReturnBlocks(stripped)) {
    const simplified = scanAttributeStrings(
      stripAttributeExpressions(block, violations),
      violations,
    );
    scanRegion(simplified, violations, constInitializers);
  }
  return violations;
}

describe('all strings from messages', () => {
  it('the scan detects a rendering-position string literal', () => {
    const body =
      'if (x) { return <button type="button">{cond ? \'Sí\' : MESSAGES.CANCEL}</button>; }';
    expect(strayLiteralsFromSource(body)).toEqual(["'Sí'"]);
  });

  it('the scan detects bare JSX text and ignores punctuation-only text', () => {
    const body = 'return <p>Lista vacia: anade un elemento</p>;';
    expect(strayLiteralsFromSource(body)).toEqual(['Lista vacia: anade un elemento']);
    expect(HAS_CONTENT.test(' - ')).toBe(false);
  });

  it('the scan ignores a same-shaped comparison operand, not a rendered branch', () => {
    const body = "return (activeView === 'week' ? <Foo /> : null);";
    expect(strayLiteralsFromSource(body)).toEqual([]);
  });

  it('the scan detects a hardcoded prop value passed to a child component (Finding 1)', () => {
    const body = 'return <EmptyState message="Todavia no hay platos para este hueco." />;';
    expect(strayLiteralsFromSource(body)).toEqual(['"Todavia no hay platos para este hueco."']);
  });

  it('the scan ignores allowlisted structural attributes (Finding 1)', () => {
    const body = 'return <button type="button" className="primary">{MESSAGES.OK}</button>;';
    expect(strayLiteralsFromSource(body)).toEqual([]);
  });

  it('the scan detects a hardcoded braced prop value (Finding 1, round 3)', () => {
    const body = "return <EmptyState message={'Todavia no hay platos.'} />;";
    expect(strayLiteralsFromSource(body)).toEqual(["'Todavia no hay platos.'"]);
  });

  it('the scan detects a hardcoded branch of a braced conditional prop (Finding 1, round 3)', () => {
    const body = "return <EmptyState message={cond ? 'Sin elementos' : MESSAGES.EMPTY} />;";
    expect(strayLiteralsFromSource(body)).toEqual(["'Sin elementos'"]);
  });

  it('the scan ignores a style object and an event handler braced prop (Finding 1, round 3)', () => {
    const body =
      "return <button style={{ color: 'flex' }} onClick={() => onSave('x')}>{MESSAGES.OK}</button>;";
    expect(strayLiteralsFromSource(body)).toEqual([]);
  });

  it('the scan detects a hardcoded template literal in a rendering position (Finding 2)', () => {
    const body = 'return <p>{cond ? `Semana actual` : MESSAGES.WEEK_LABEL_NEXT}</p>;';
    expect(strayLiteralsFromSource(body)).toEqual(['`Semana actual`']);
  });

  it('the scan ignores a pure-interpolation template literal (Finding 2)', () => {
    const body = 'return <p>{`${a}-${b}`}</p>;';
    expect(strayLiteralsFromSource(body)).toEqual([]);
  });

  it('the scan resolves a const computed above the return statement (Finding 3)', () => {
    const body =
      "const label = designation === 'next' ? MESSAGES.WEEK_LABEL_NEXT : 'Semana actual'; " +
      'return <p>{label}</p>;';
    expect(strayLiteralsFromSource(body)).toEqual(["'Semana actual'"]);
  });

  it('the scan does not flag a const that only reaches MESSAGES (Finding 3)', () => {
    const body =
      "const label = designation === 'next' ? MESSAGES.WEEK_LABEL_NEXT : MESSAGES.WEEK_LABEL_CURRENT; " +
      'return <p>{label}</p>;';
    expect(strayLiteralsFromSource(body)).toEqual([]);
  });

  it('the scan detects bare text with a parenthetical aside (Finding 5)', () => {
    const body = 'return <p>Cantidad (unidades)</p>;';
    expect(strayLiteralsFromSource(body)).toEqual(['Cantidad (unidades)']);
  });

  it('the scan still ignores a ternary/map gap that happens to contain parens', () => {
    const body =
      'return (cond ? (\n' +
      '  <A />\n' +
      ') : (\n' +
      '  items.map((x) => (\n' +
      '    <B />\n' +
      '  ))\n' +
      '));';
    expect(strayLiteralsFromSource(body)).toEqual([]);
  });

  it('no frontend/src/components/**/*.jsx file hardcodes a JSX-text literal outside MESSAGES (R15)', () => {
    const offenders = jsxFiles(COMPONENTS_DIR)
      .map((path) => [path, strayLiterals(path)])
      .filter(([, literals]) => literals.length > 0);

    expect(offenders).toEqual([]);
  });
});

// Test-only helper mirroring `strayLiterals`, for the self-check fixtures
// above that pass raw source text instead of a file path.
function strayLiteralsFromSource(source) {
  const violations = [];
  const constInitializers = collectConstInitializers(source);
  for (const block of extractReturnBlocks(source)) {
    const simplified = scanAttributeStrings(
      stripAttributeExpressions(block, violations),
      violations,
    );
    scanRegion(simplified, violations, constInitializers);
  }
  return violations;
}
