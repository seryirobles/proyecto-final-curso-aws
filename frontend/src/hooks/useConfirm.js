// Confirmation-gate state machine for R18 - every destructive handler calls
// `requestConfirm` instead of the API directly (design.md section 4.4).
// No `window.confirm` (rejected, design.md section 7): a native dialog is a
// global side effect a hook cannot expose as state.

import { useState } from 'react';

export function useConfirm() {
  const [pending, setPending] = useState(null); // { message, onConfirm } | null

  return {
    pending,
    requestConfirm: (message, onConfirm) => setPending({ message, onConfirm }),
    confirm: () => {
      pending?.onConfirm();
      setPending(null);
    },
    cancel: () => setPending(null),
  };
}
