// The shopping list screen (T36; design.md section 5): unchecked then
// checked sections (FR-SHOP-08, checked items greyed via tokens.color.ink3),
// add/edit/remove, and a week-scoped resync button (R21, FR-SHOP-05).

import { tokens } from '../tokens/index.js';
import { MESSAGES } from '../messages/index.js';
import { UNIT_LABELS } from '../domain/labels.js';
import {
  selectStyle,
  inputStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  ghostButtonStyle,
  listRowStyle,
  listResetStyle,
  cardStyle,
  headingStyle,
} from '../tokens/controlStyles.js';
import { EmptyState } from './EmptyState.jsx';
import { LoadingState } from './LoadingState.jsx';
import { ConfirmDialog } from './ConfirmDialog.jsx';
import { WeekLabel } from './WeekLabel.jsx';

function ItemRow({ item, onToggle, onEdit, onRemove }) {
  return (
    <li
      style={{
        ...listRowStyle,
        ...(item.checked ? { color: tokens.color.ink3, textDecoration: 'line-through' } : null),
      }}
    >
      <input
        type="checkbox"
        checked={item.checked}
        onChange={() => onToggle(item, !item.checked)}
      />
      <span style={{ flex: 1 }}>
        {item.name} · {item.quantity} {UNIT_LABELS[item.unit] ?? item.unit}
      </span>
      {!item.checked ? (
        <button type="button" onClick={() => onEdit(item)} style={ghostButtonStyle}>
          {MESSAGES.SHOPPING_LIST_EDIT}
        </button>
      ) : null}
      <button type="button" onClick={() => onRemove(item.id)} style={ghostButtonStyle}>
        {MESSAGES.SHOPPING_LIST_REMOVE}
      </button>
    </li>
  );
}

const sectionCardStyle = { ...cardStyle, marginTop: tokens.space.md };

function ResyncScope({ liveWeeks, isResyncing, resync }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: tokens.space.sm }}>
      <span>{MESSAGES.SHOPPING_LIST_RESYNC_SCOPE_LABEL}</span>
      {liveWeeks ? (
        <>
          <WeekLabel
            designation="current"
            monday={liveWeeks.current.monday}
            sunday={liveWeeks.current.sunday}
          />
          <span>{MESSAGES.SHOPPING_LIST_RESYNC_SCOPE_CONNECTOR}</span>
          <WeekLabel
            designation="next"
            monday={liveWeeks.next.monday}
            sunday={liveWeeks.next.sunday}
          />
        </>
      ) : null}
      <button
        type="button"
        onClick={resync}
        disabled={isResyncing}
        style={primaryButtonStyle(isResyncing)}
      >
        {MESSAGES.SHOPPING_LIST_RESYNC}
      </button>
      {isResyncing ? <LoadingState message={MESSAGES.SHOPPING_LIST_RESYNC_IN_PROGRESS} /> : null}
    </div>
  );
}

function ItemForm({ isEditing, draft, updateDraftField, canSaveItem, saveItem, closeForm }) {
  return (
    <div
      style={{
        padding: tokens.space.md,
        backgroundColor: tokens.color.surface,
        border: `1px solid ${tokens.color.line}`,
        borderRadius: tokens.radius.md,
        boxShadow: tokens.shadow.sm,
        marginTop: tokens.space.md,
      }}
    >
      <label>
        {MESSAGES.SHOPPING_LIST_NAME_LABEL}
        <input
          type="text"
          value={draft.name}
          onChange={(e) => updateDraftField('name', e.target.value)}
          style={inputStyle}
        />
      </label>
      <label>
        {MESSAGES.SHOPPING_LIST_QUANTITY_LABEL}
        <input
          type="number"
          value={draft.quantity}
          onChange={(e) => updateDraftField('quantity', e.target.value)}
          style={inputStyle}
        />
      </label>
      <label>
        {MESSAGES.SHOPPING_LIST_UNIT_LABEL}
        <select
          value={draft.unit}
          onChange={(e) => updateDraftField('unit', e.target.value)}
          style={selectStyle}
        >
          <option value="">{MESSAGES.SHOPPING_LIST_UNIT_PLACEHOLDER}</option>
          {Object.entries(UNIT_LABELS).map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <div style={{ display: 'flex', gap: tokens.space.sm, marginTop: tokens.space.md }}>
        <button
          type="button"
          onClick={saveItem}
          disabled={!canSaveItem}
          style={primaryButtonStyle(!canSaveItem)}
        >
          {isEditing ? MESSAGES.SHOPPING_LIST_SAVE_EDIT : MESSAGES.SHOPPING_LIST_SAVE_ADD}
        </button>
        <button type="button" onClick={closeForm} style={secondaryButtonStyle}>
          {MESSAGES.SHOPPING_LIST_CANCEL}
        </button>
      </div>
    </div>
  );
}

export function ShoppingListView({
  uncheckedItems,
  checkedItems,
  isLoading,
  liveWeeks,
  isFormOpen,
  isEditing,
  draft,
  updateDraftField,
  canSaveItem,
  openAdd,
  openEdit,
  closeForm,
  saveItem,
  setChecked,
  remove,
  confirm,
  isResyncing,
  resync,
  error,
}) {
  if (isLoading) return <LoadingState />;

  const isEmpty = uncheckedItems.length === 0 && checkedItems.length === 0;

  return (
    <div>
      <h2
        style={{
          margin: tokens.space.none,
          fontFamily: tokens.fontFamily.heading,
          fontSize: tokens.fontSize.xl,
        }}
      >
        {MESSAGES.SHOPPING_LIST_VIEW_TITLE}
      </h2>
      {error ? <p style={{ color: tokens.color.ink, padding: tokens.space.md }}>{error}</p> : null}

      <ResyncScope liveWeeks={liveWeeks} isResyncing={isResyncing} resync={resync} />

      <button
        type="button"
        onClick={openAdd}
        style={{ ...primaryButtonStyle(false), marginTop: tokens.space.sm }}
      >
        {MESSAGES.SHOPPING_LIST_ADD}
      </button>

      {isEmpty ? (
        <EmptyState message={MESSAGES.SHOPPING_LIST_VIEW_EMPTY} />
      ) : (
        <>
          <div style={sectionCardStyle}>
            <h3 style={headingStyle}>{MESSAGES.SHOPPING_LIST_UNCHECKED_SECTION_TITLE}</h3>
            <ul style={listResetStyle}>
              {uncheckedItems.map((item) => (
                <ItemRow
                  key={item.id}
                  item={item}
                  onToggle={setChecked}
                  onEdit={openEdit}
                  onRemove={remove}
                />
              ))}
            </ul>
          </div>

          <div style={sectionCardStyle}>
            <h3 style={headingStyle}>{MESSAGES.SHOPPING_LIST_CHECKED_SECTION_TITLE}</h3>
            <ul style={listResetStyle}>
              {checkedItems.map((item) => (
                <ItemRow
                  key={item.id}
                  item={item}
                  onToggle={setChecked}
                  onEdit={openEdit}
                  onRemove={remove}
                />
              ))}
            </ul>
          </div>
        </>
      )}

      {isFormOpen ? (
        <ItemForm
          isEditing={isEditing}
          draft={draft}
          updateDraftField={updateDraftField}
          canSaveItem={canSaveItem}
          saveItem={saveItem}
          closeForm={closeForm}
        />
      ) : null}

      <ConfirmDialog
        pending={confirm.pending}
        onConfirm={confirm.confirm}
        onCancel={confirm.cancel}
      />
    </div>
  );
}
