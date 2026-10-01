// Shared name/category filter markup (F6 fix round 1): design.md section 5's
// Screens table maps LibraryView to "+ LibraryRecipePicker", implying reuse -
// LibraryRecipePicker and LibraryView both render this, not a hand copy each.

// Icon-prefixed search box + pill-shaped category select (T86, design.md
// 10.6) - previously zero token references at all, the most under-styled
// component in the audit. Mined from the prototype's filter row, not ported.

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS } from '../domain/labels.js';

function SearchIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <circle cx="11" cy="11" r="6.5" />
      <path d="M20 20l-4-4" />
    </svg>
  );
}

const searchBoxStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: tokens.space.xs,
  flex: '1',
  minWidth: '160px',
  border: `1px solid ${tokens.color.line2}`,
  backgroundColor: tokens.color.surface,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  color: tokens.color.ink3,
};

const filterLabelTextStyle = {
  fontFamily: tokens.fontFamily.label,
  fontSize: tokens.fontSize.xs,
  color: tokens.color.ink3,
  whiteSpace: 'nowrap',
};

const searchInputStyle = {
  boxSizing: 'border-box',
  border: 'none',
  backgroundColor: 'transparent',
  flex: '1',
  color: tokens.color.ink,
  fontSize: tokens.fontSize.input,
};

const categorySelectStyle = {
  boxSizing: 'border-box',
  border: `1px solid ${tokens.color.line}`,
  backgroundColor: tokens.color.surface2,
  color: tokens.color.ink2,
  borderRadius: tokens.radius.pill,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontSize: tokens.fontSize.input,
  fontWeight: 700,
};

export function LibraryFilters({ filters, setName, setCategory }) {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: tokens.space.sm,
        marginBottom: tokens.space.md,
      }}
    >
      <label style={searchBoxStyle}>
        <SearchIcon />
        <span style={filterLabelTextStyle}>{MESSAGES.LIBRARY_PICKER_NAME_LABEL}</span>
        <input
          type="text"
          value={filters.name}
          onChange={(e) => setName(e.target.value)}
          style={searchInputStyle}
        />
      </label>
      <label style={{ display: 'flex', alignItems: 'center', gap: tokens.space.xs }}>
        <span style={filterLabelTextStyle}>{MESSAGES.LIBRARY_PICKER_CATEGORY_LABEL}</span>
        <select
          value={filters.category}
          onChange={(e) => setCategory(e.target.value)}
          style={categorySelectStyle}
        >
          <option value="">{MESSAGES.LIBRARY_PICKER_CATEGORY_ALL}</option>
          {Object.entries(CATEGORY_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
