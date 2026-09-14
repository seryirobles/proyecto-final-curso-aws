// Shared name/category filter markup (F6 fix round 1): design.md section 5's
// Screens table maps LibraryView to "+ LibraryRecipePicker", implying reuse -
// LibraryRecipePicker and LibraryView both render this, not a hand copy each.

import { MESSAGES } from '../messages/index.js';
import { CATEGORY_LABELS } from '../domain/labels.js';

export function LibraryFilters({ filters, setName, setCategory }) {
  return (
    <div>
      <label>
        {MESSAGES.LIBRARY_PICKER_NAME_LABEL}
        <input type="text" value={filters.name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label>
        {MESSAGES.LIBRARY_PICKER_CATEGORY_LABEL}
        <select value={filters.category} onChange={(e) => setCategory(e.target.value)}>
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
