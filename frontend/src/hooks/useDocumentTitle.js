// Sets document.title: "<view label> · <app title>" for a User, else the app
// title (frontend_ux_phase2 R18, R19).

import { useEffect } from 'react';
import { MESSAGES } from '../messages/index.js';

export function useDocumentTitle(viewLabel) {
  useEffect(() => {
    document.title = viewLabel
      ? MESSAGES.DOCUMENT_TITLE(viewLabel, MESSAGES.APP_TITLE)
      : MESSAGES.APP_TITLE;
  }, [viewLabel]);
}
