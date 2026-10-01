// The week view's candidate authoring flow (issue add-dish-button-inert,
// plan.md "Fix design"): mounted only while a slot is being authored, so its
// useRecipeAuthoring instance (and the useLibraryPicker polls inside it)
// exist only then - same reasoning as LibraryView's isAuthoringOpen guard.

import { useRef } from 'react';
import { useRecipeAuthoring } from '../hooks/useRecipeAuthoring.js';
import { RecipeAuthoringForm } from './RecipeAuthoringForm.jsx';
import { MESSAGES } from '../messages/index.js';
import { tokens } from '../tokens/index.js';
import { secondaryButtonStyle, headingStyle } from '../tokens/controlStyles.js';
import { useScrollIntoView } from '../hooks/useScrollIntoView.js';
import { DAY_LABELS, SLOT_LABELS } from '../domain/labels.js';

// `initialRecipe` set (edit path, scope extension) opens straight on the
// from-scratch tab, seeded with the meal's own content (E5).
export function CandidateAuthoring({ onSubmit, onClose, initialRecipe = null, target = null }) {
  const authoring = useRecipeAuthoring({
    mode: 'candidate',
    onSubmit,
    initialRecipe,
    initialMethod: initialRecipe ? 'scratch' : null,
    aiTarget: target,
  });

  const ref = useRef(null);
  const key = target
    ? `${target.weekId}:${target.day}:${target.slot}:${target.candidateId ?? 'new'}`
    : null;
  useScrollIntoView(ref, key);
  const title = target
    ? (initialRecipe ? MESSAGES.EDIT_CANDIDATE_TITLE : MESSAGES.ADD_CANDIDATE_TITLE)(
        DAY_LABELS[target.day],
        SLOT_LABELS[target.slot],
      )
    : null;

  return (
    <section ref={ref}>
      {title ? <h3 style={headingStyle}>{title}</h3> : null}
      <RecipeAuthoringForm {...authoring} />
      <button
        type="button"
        onClick={onClose}
        style={{ ...secondaryButtonStyle, marginTop: tokens.space.sm }}
      >
        {MESSAGES.RECIPE_DETAIL_CLOSE}
      </button>
    </section>
  );
}
