import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface BreadcrumbItem {
  label: string;
  path?: string;
}

interface MainLayoutProps {
  children: React.ReactNode;
  breadcrumb?: BreadcrumbItem[];
}

// ── Resizable panel constraints ───────────────────────────────────────────────
const GUIDANCE_MIN = 180;   // px — narrowest the suggestion panel can go
const GUIDANCE_MAX = 520;   // px — widest it can go
const GUIDANCE_DEFAULT = 300; // px — starting width

const MainLayout: React.FC<MainLayoutProps> = ({ children, breadcrumb }) => {
  const location = useLocation();
  const isAiPage = location.pathname === '/ai-assistant';

  // ── Nav collapse state ────────────────────────────────────────────────────
  const [navCollapsed, setNavCollapsed] = useState(() => {
    // Read saved preference on first render
    return localStorage.getItem('navCollapsed') === 'true' || window.innerWidth < 992;
  });

  // FIX 1: Sync navCollapsed → document.body class.
  // Your existing CSS uses  body.nav-collapsed .nav-panel { transform: translateX(-100%) }
  // and  body.nav-collapsed .main-wrapper { margin-left: var(--icon-bar-width) }
  // Toggling the body class means ALL that CSS works with zero changes.
  useEffect(() => {
    if (navCollapsed) {
      document.body.classList.add('nav-collapsed');
    } else {
      document.body.classList.remove('nav-collapsed');
    }
  }, [navCollapsed]);

  // Collapse on small screens automatically
  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < 992) setNavCollapsed(true);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const toggleNav = () => {
    setNavCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('navCollapsed', String(next));
      return next;
    });
  };

  // ── Guidance panel resize state ───────────────────────────────────────────
  const [guidanceWidth, setGuidanceWidth] = useState(GUIDANCE_DEFAULT);

  // Use refs for drag tracking — avoids re-renders during mousemove
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(GUIDANCE_DEFAULT);

  const onHandleMouseDown = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    startX.current = e.clientX;
    startWidth.current = guidanceWidth;
    // Prevent text selection while dragging
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  }, [guidanceWidth]);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const delta = e.clientX - startX.current;
      const next = Math.min(GUIDANCE_MAX, Math.max(GUIDANCE_MIN, startWidth.current + delta));
      setGuidanceWidth(next);
    };

    const onMouseUp = () => {
      if (!isDragging.current) return;
      isDragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, []);

  const isActive = (path: string) => location.pathname === path;

  const navLinks = [
    { to: '/',            icon: 'bi-house-door',    label: 'Home' },
    { to: '/portfolio',   icon: 'bi-person-vcard',   label: 'Portfolio' },
    { to: '/survey',      icon: 'bi-ui-checks',      label: 'Student Survey' },
    { to: '/ai-assistant',icon: 'bi-stars',           label: 'AI Survey Assistant' },
    { to: '/contact',     icon: 'bi-envelope',        label: 'Contact' },
  ];

  return (
    <>
      {/* ── Icon bar (always visible) ───────────────────────────────────── */}
      <aside className="icon-bar">
        <Link to="/" className="brand">VS</Link>
        <ul className="icon-bar-nav">
          {navLinks.map(({ to, icon, label }) => (
            <li key={to} className="icon-bar-item">
              <Link
                className={`icon-bar-link${isActive(to) ? ' active' : ''}`}
                to={to}
                title={label}
              >
                <i className={`bi ${icon}`} />
                <span className="tooltip-text">{label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </aside>

      {/* ── Slide-out nav panel ─────────────────────────────────────────── */}
      <aside className="nav-panel" id="navPanel">
        <div className="nav-panel-header">
          <h4>VSTech Solutions</h4>
          <span>Personal Dashboard</span>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Main Navigation</div>
          <ul className="nav-menu">
            {navLinks.map(({ to, icon, label }) => (
              <li key={to} className="nav-menu-item">
                <Link
                  className={`nav-menu-link${isActive(to) ? ' active' : ''}`}
                  to={to}
                >
                  <i className={`bi ${icon}`} />
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Quick Links</div>
          <ul className="nav-menu">
            <li className="nav-menu-item">
              <a className="nav-menu-link" href="https://github.com/vivek-sarvagod?tab=repositories" target="_blank" rel="noreferrer">
                <i className="bi bi-github" /> GitHub Profile
              </a>
            </li>
            <li className="nav-menu-item">
              <a className="nav-menu-link" href="https://linkedin.com/in/vivek-sarvagod" target="_blank" rel="noreferrer">
                <i className="bi bi-linkedin" /> LinkedIn
              </a>
            </li>
          </ul>
        </div>

        <div className="nav-user">
          <div className="nav-user-info">
            <div className="nav-user-avatar">VS</div>
            <div className="nav-user-details">
              <div className="name">Vivek Sarvagod</div>
              <div className="role">Software Architect</div>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main wrapper ────────────────────────────────────────────────── */}
      <div className="main-wrapper">
        <header className="main-header">
          <div className="header-left">
            {/* FIX 1: button now correctly toggles nav via body class */}
            <button
              className="menu-toggle"
              onClick={toggleNav}
              aria-label="Toggle navigation"
              aria-expanded={!navCollapsed}
            >
              <i className="bi bi-list" />
            </button>
            <nav className="breadcrumb-nav">
              {breadcrumb && breadcrumb.length > 0 ? (
                breadcrumb.map((crumb, idx) => (
                  <React.Fragment key={idx}>
                    {idx > 0 && <span>/</span>}
                    {crumb.path ? (
                      <Link to={crumb.path}>{crumb.label}</Link>
                    ) : (
                      <span className={idx === breadcrumb.length - 1 ? 'current' : ''}>
                        {crumb.label}
                      </span>
                    )}
                  </React.Fragment>
                ))
              ) : (
                <Link to="/">Home</Link>
              )}
            </nav>
          </div>
        </header>

        <main className="main-content">
          {isAiPage ? (
            /*
             * FIX 2: Wrap the AI page in a relative-positioned div that:
             *   a) passes --guidance-w down to .ai-assistant-shell's grid
             *   b) acts as the containing block for the absolute resize handle
             * We do NOT use display:contents here because that breaks
             * absolute positioning of the drag handle child.
             */
            <div
              className="ai-resizable-shell"
              style={{ '--guidance-w': `${guidanceWidth}px` } as React.CSSProperties}
            >
              {children}
              <div
                className="resize-handle"
                onMouseDown={onHandleMouseDown}
                title="Drag to resize panels"
                role="separator"
                aria-orientation="vertical"
              />
            </div>
          ) : (
            children
          )}
        </main>
      </div>
    </>
  );
};

export default MainLayout;