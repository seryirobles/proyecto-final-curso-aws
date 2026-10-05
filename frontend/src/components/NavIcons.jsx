// Decorative tab bar icons (frontend_ux_phase2 R10): no aria, no role; the
// visible label beside them is the button's accessible name.

const ICON_PROPS = {
  viewBox: '0 0 24 24',
  width: 20,
  height: 20,
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

const ICON_PATHS = {
  week: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </>
  ),
  library: (
    <path d="M4 4h6a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4zM20 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z" />
  ),
  rules: <path d="M4 6h16M4 12h16M4 18h16" />,
  shoppingList: (
    <>
      <path d="M3 4h2l2.5 11h10L20 7H6" />
      <circle cx="9" cy="19" r="1" />
      <circle cx="17" cy="19" r="1" />
    </>
  ),
  summary: <path d="M5 4h14v16H5zM9 9h6M9 13h6M9 17h3" />,
};

export function NavIcon({ view }) {
  return <svg {...ICON_PROPS}>{ICON_PATHS[view]}</svg>;
}
