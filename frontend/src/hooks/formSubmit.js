// Native-form submit guard (frontend_ux_phase1 R25, R26): always stop the
// browser navigation, run the action only while submission is allowed.

export function handleFormSubmit(event, canSubmit, action) {
  event.preventDefault();
  if (!canSubmit) return;
  action();
}
