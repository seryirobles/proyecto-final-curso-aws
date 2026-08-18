import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { PlaceholderView } from '../src/PlaceholderView.jsx';
import { MESSAGES } from '../src/messages/index.js';

describe('PlaceholderView', () => {
  it('renders the scaffold placeholder copy sourced from the messages module', () => {
    const markup = renderToStaticMarkup(<PlaceholderView />);

    expect(markup).toContain(MESSAGES.SCAFFOLD_PLACEHOLDER_TITLE);
    expect(markup).toContain(MESSAGES.SCAFFOLD_PLACEHOLDER_BODY);
  });
});
