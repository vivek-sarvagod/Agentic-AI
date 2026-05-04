// components/agent/AgentBubble.tsx
// ----------------------------------
// Renders a single assistant chat bubble.
// Reads ui_hints to decide which rich components to show below the text.
//
// COMPONENT HIERARCHY
// -------------------
// AgentBubble
//   ├── AgentTags          (coloured "Campus info agent" pills)
//   ├── <pre> text content
//   ├── CampusMapCard      (Google Maps embed + address)
//   ├── InfoChips          (Founded · 1972, Students · 40k+, …)
//   ├── SiteLinkCard       (clickable official site card)
//   ├── AnalyticsCharts    (bar charts from recharts)
//   ├── ConfirmButtons     (Yes / No for write actions)
//   └── QuickActions       (suggestion prompt buttons)

import React from 'react';
import type { ChatMessage } from '../../types/agent';
import AgentTags from './AgentTags';
import CampusMapCard from './CampusMapCard';
import InfoChips from './InfoChips';
import SiteLinkCard from './SiteLinkCard';
import AnalyticsCharts from './AnalyticsCharts';

interface Props {
  message: ChatMessage;
  onQuickAction: (prompt: string) => void;
}

const AgentBubble: React.FC<Props> = ({ message, onQuickAction }) => {
  const hints = message.ui_hints ?? {};

  return (
    <div className="chat-message assistant">
      <div className="chat-avatar">
        <i className="bi bi-stars" />
      </div>

      <div className="chat-bubble agent-bubble">
        {/* Coloured agent tag pills at the top */}
        {message.agent_tags && message.agent_tags.length > 0 && (
          <AgentTags tags={message.agent_tags} />
        )}

        {/* Main plain-text response */}
        <pre className="bubble-text">{message.content}</pre>

        {/* Google Maps embed — only when campus_info ran with location data */}
        {hints.show_map && hints.map && (
          <CampusMapCard map={hints.map} />
        )}

        {/* Fact chips — Founded, Students, Programs, etc. */}
        {hints.show_info_chips && hints.chips && hints.chips.length > 0 && (
          <InfoChips chips={hints.chips} />
        )}

        {/* Official site link card */}
        {hints.show_link_card && hints.link_card && (
          <SiteLinkCard card={hints.link_card} />
        )}

        {/* Analytics bar charts */}
        {hints.show_charts && hints.charts && hints.charts.length > 0 && (
          <AnalyticsCharts charts={hints.charts} />
        )}

        {/* Confirmation yes/no buttons */}
        {message.requires_confirmation && (
          <div className="confirmation-actions">
            <button type="button" onClick={() => onQuickAction('yes')}>
              <i className="bi bi-check2" /> Yes
            </button>
            <button type="button" onClick={() => onQuickAction('no')}>
              <i className="bi bi-x-lg" /> No
            </button>
          </div>
        )}

        {/* Suggestion buttons */}
        {message.quick_actions && message.quick_actions.length > 0 && (
          <div className="quick-actions">
            {message.quick_actions.map((action) => (
              <button
                key={action.prompt}
                type="button"
                className="quick-action-btn"
                onClick={() => onQuickAction(action.prompt)}
              >
                {action.label} ↗
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentBubble;
