import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { PlaceholderView } from './PlaceholderView.jsx';

const container = document.getElementById('root');

createRoot(container).render(
  <StrictMode>
    <PlaceholderView />
  </StrictMode>,
);
