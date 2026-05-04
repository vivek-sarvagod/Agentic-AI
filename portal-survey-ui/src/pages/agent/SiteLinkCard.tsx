// components/agent/SiteLinkCard.tsx
// -----------------------------------
// A clickable card linking to the campus official website.
// Optionally shows a second link to the admissions page.

import React from 'react';
import type { LinkCard } from '../../types/agent';

interface Props {
  card: LinkCard;
}

const SiteLinkCard: React.FC<Props> = ({ card }) => (
  <div className="site-link-card">
    <div className="site-link-card__body">
      <div className="site-link-card__icon">
        <i className="bi bi-globe" />
      </div>
      <div className="site-link-card__text">
        <strong>{card.title}</strong>
        <span>{card.description}</span>
      </div>
    </div>

    <div className="site-link-card__actions">
      <a
        href={card.url}
        target="_blank"
        rel="noreferrer"
        className="site-link-btn"
      >
        <i className="bi bi-box-arrow-up-right" /> Official site
      </a>
      {card.admissions_url && (
        <a
          href={card.admissions_url}
          target="_blank"
          rel="noreferrer"
          className="site-link-btn"
        >
          <i className="bi bi-mortarboard" /> Admissions
        </a>
      )}
    </div>
  </div>
);

export default SiteLinkCard;
