// components/agent/AgentTags.tsx
// --------------------------------
// Renders small coloured pills showing which agents handled the message.
// e.g. ["Campus info agent", "Analytics agent"]
//
// COLOUR LOGIC
// ------------
// Each agent name maps to a CSS class. Add new agents to AGENT_COLOURS
// and add the matching CSS rule in AISurveyAssistantPage.css.

import React from 'react';

interface Props {
  tags: string[];
}

// Maps agent display label → CSS modifier class
const AGENT_COLOURS: Record<string, string> = {
  'Survey agent': 'tag--crud',
  'Analytics agent': 'tag--analytics',
  'Campus info agent': 'tag--campus',
  'Insight agent': 'tag--insight',
};

const AgentTags: React.FC<Props> = ({ tags }) => (
  <div className="agent-tags">
    {tags.map((tag) => (
      <span
        key={tag}
        className={`agent-tag ${AGENT_COLOURS[tag] ?? 'tag--default'}`}
      >
        {tag}
      </span>
    ))}
  </div>
);

export default AgentTags;
