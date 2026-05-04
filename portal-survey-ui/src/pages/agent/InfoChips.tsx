// components/agent/InfoChips.tsx
// --------------------------------
// Renders a row of small pill badges showing campus facts.
// e.g. "Founded · 1972"  "Students · 40,000+"  "Programs · 200+"

import React from 'react';
import type { Chip } from '../../types/agent';

interface Props {
  chips: Chip[];
}

const InfoChips: React.FC<Props> = ({ chips }) => (
  <div className="info-chips">
    {chips.map((chip) => (
      <span key={chip.label} className="info-chip">
        <strong>{chip.label}</strong> · {chip.value}
      </span>
    ))}
  </div>
);

export default InfoChips;
