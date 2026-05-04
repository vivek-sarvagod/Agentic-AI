// components/agent/CampusMapCard.tsx
// -------------------------------------
// Renders a Google Maps embed iframe + address line + action links.
// Only shown when the campus_info agent returns a location result.
//
// NOTE ON THE IFRAME
// ------------------
// We use embed_url (the ?output=embed variant) so the map renders
// inline without requiring a Maps JavaScript API key.
// The iframe src never includes an API key — it uses Google's
// free embed tier which is sufficient for this use case.

import React from 'react';
import type { MapData } from '../../types/agent';

interface Props {
  map: MapData;
}

const CampusMapCard: React.FC<Props> = ({ map }) => (
  <div className="campus-map-card">
    {/* Embedded map */}
    <div className="map-embed-wrapper">
      <iframe
        title={`Map of ${map.label}`}
        src={map.embed_url}
        width="100%"
        height="200"
        style={{ border: 0, borderRadius: '8px' }}
        allowFullScreen
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />
    </div>

    {/* Address + action links below the map */}
    <div className="map-footer">
      <span className="map-address">
        <i className="bi bi-geo-alt" /> {map.address}
      </span>
      <div className="map-links">
        <a
          href={map.maps_link}
          target="_blank"
          rel="noreferrer"
          className="map-link-btn"
        >
          <i className="bi bi-box-arrow-up-right" /> Open in Maps
        </a>
      </div>
    </div>
  </div>
);

export default CampusMapCard;
