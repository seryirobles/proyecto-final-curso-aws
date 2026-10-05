// Selected day + card refs for the day strip (frontend_ux_phase2 R33, R34).

import { useCallback, useRef, useState } from 'react';

export function useDayStrip() {
  const refs = useRef({});
  const [selectedDay, setSelectedDay] = useState(null);

  const registerDay = useCallback(
    (day) => (node) => {
      refs.current[day] = node;
    },
    [],
  );

  const scrollToDay = useCallback((day) => {
    setSelectedDay(day);
    refs.current[day]?.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }, []);

  return { registerDay, scrollToDay, selectedDay };
}
