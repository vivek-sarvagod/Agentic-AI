"""
shared/tools/campus_tool.py
----------------------------
Dynamic campus data resolution — works for ANY university worldwide.

HOW IT WORKS (end to end)
--------------------------
User types: "Where is MIT located?"
                    │
                    ▼
        extract_university_name()
        Regex + keyword stripping → "MIT"
                    │
                    ▼
        resolve_campus(name, query_type)
                    │
             ┌──────┴──────┐
             │             │
        CAMPUS_DB      web_search_university()
        (instant,      DuckDuckGo → parse coords,
         zero cost)    official URL, facts
             │             │
             └──────┬──────┘
                    ▼
         Normalised campus dict
         {name, location{lat,lng,...},
          facts, official_url, ...}
                    │
                    ▼
         CampusInfoAgent builds result

KEY DESIGN DECISIONS
---------------------
1. CAMPUS_DB is kept as a fast-path cache for known campuses.
   We pre-populate GMU (the portal's home campus) so it always
   works instantly with zero network calls.

2. For unknown universities, we do TWO DuckDuckGo searches:
   - "{university} location address coordinates"  → extract lat/lng
   - "{university} official website founded students" → extract facts
   We parse the plain-text snippets with regex — no API key needed.

3. Coordinates are extracted from:
   - Decimal patterns like "38.8308, -77.3075"
   - Wikipedia/Google Knowledge Panel snippets that contain them
   If we can't find real coords, we fall back to a Maps search URL
   so the user still gets a working link.

4. The returned dict has the SAME shape as a CAMPUS_DB entry so
   CampusInfoAgent needs zero changes when switching between
   static and dynamic campuses.

ADDING A NEW KNOWN CAMPUS
--------------------------
Just add an entry to CAMPUS_DB. That's it.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Static fast-path cache ────────────────────────────────────────────────────
# Pre-populated for known campuses. Extend this freely.
CAMPUS_DB: dict[str, dict[str, Any]] = {
    "gmu": {
        "name": "George Mason University",
        "short_name": "GMU",
        "official_url": "https://www.gmu.edu",
        "admissions_url": "https://www2.gmu.edu/admissions-aid",
        "location": {
            "address": "4400 University Dr, Fairfax, VA 22030",
            "city": "Fairfax",
            "state": "Virginia",
            "lat": 38.8308,
            "lng": -77.3075,
        },
        "facts": {
            "founded": "1972",
            "students": "40,000+",
            "programs": "200+ degree programs",
            "type": "Public research university",
            "nickname": "Patriots",
        },
        "maps_embed_url": "https://maps.google.com/maps?q=38.8308,-77.3075&output=embed&z=15",
        "maps_link": "https://maps.google.com/?q=38.8308,-77.3075",
    },
    "george mason": {
        # Alias — same entry
        "name": "George Mason University",
        "short_name": "GMU",
        "official_url": "https://www.gmu.edu",
        "admissions_url": "https://www2.gmu.edu/admissions-aid",
        "location": {
            "address": "4400 University Dr, Fairfax, VA 22030",
            "city": "Fairfax",
            "state": "Virginia",
            "lat": 38.8308,
            "lng": -77.3075,
        },
        "facts": {
            "founded": "1972",
            "students": "40,000+",
            "programs": "200+ degree programs",
            "type": "Public research university",
            "nickname": "Patriots",
        },
        "maps_embed_url": "https://maps.google.com/maps?q=38.8308,-77.3075&output=embed&z=15",
        "maps_link": "https://maps.google.com/?q=38.8308,-77.3075",
    },
}

# Fallback when no university can be extracted from the query
DEFAULT_CAMPUS_KEY = "gmu"

# ── University name extraction ───────────────────────────────────────────────

def extract_university_name(query: str) -> str:
    """
    Pull the university / campus name out of a natural language query.

    Strategy (in order):
    a) Abbreviation map  (MIT, UCLA, GMU, JHU, …)  — fastest, most reliable
    b) Trigger patterns  ("about Stanford", "where is Harvard", "MIT campus")
    c) "University/College of X" form ("University of Virginia")
    d) "X State / X Tech" names ("Penn State", "Virginia Tech")
    e) Two consecutive Title-Case words ("Johns Hopkins")

    Returns a clean string like "MIT" or "Stanford University" or "".
    """
    # ── a) Abbreviation map (checked first) ──────────────────────────────
    abbreviations: dict[str, str] = {
        r"\bMIT\b":  "MIT",
        r"\bUCLA\b": "UCLA",
        r"\bNYU\b":  "NYU",
        r"\bUSC\b":  "University of Southern California",
        r"\bGMU\b":  "George Mason University",
        r"\bGWU\b":  "George Washington University",
        r"\bUVA\b":  "University of Virginia",
        r"\bVT\b":   "Virginia Tech",
        r"\bUMD\b":  "University of Maryland",
        r"\bJHU\b":  "Johns Hopkins University",
        r"\bCMU\b":  "Carnegie Mellon University",
        r"\bUNC\b":  "University of North Carolina",
        r"\bUCF\b":  "University of Central Florida",
        r"\bFSU\b":  "Florida State University",
        r"\bOSU\b":  "Ohio State University",
        r"\bPSU\b":  "Penn State University",
        r"\bBU\b":   "Boston University",
        r"\bBC\b":   "Boston College",
        r"\bUCSB\b": "UC Santa Barbara",
        r"\bUCSD\b": "UC San Diego",
        r"\bUCB\b":  "UC Berkeley",
        r"\bCU\b":   "Columbia University",
        r"\bNU\b":   "Northwestern University",
    }
    for pattern, full_name in abbreviations.items():
        if re.search(pattern, query, re.IGNORECASE):
            return full_name

    # ── b) "University of X" / "College of X" — checked BEFORE triggers ─────
    # These start-of-sentence forms ("University of Virginia address") must be
    # caught before the trigger patterns accidentally grab just "Virginia".
    uni_of = re.search(
        r"\b(University\s+of\s+[A-Z][A-Za-z\s]{2,30}|"
        r"College\s+of\s+[A-Z][A-Za-z\s]{2,20}|"
        r"Institute\s+of\s+[A-Z][A-Za-z\s]{2,20})",
        query
    )
    if uni_of:
        # Trim trailing noise words
        candidate = uni_of.group(1).strip()
        for noise in (" address", " location", " programs", " website", " campus"):
            if candidate.lower().endswith(noise):
                candidate = candidate[: -len(noise)].strip()
        return candidate

    # ── c) Trigger-word patterns ──────────────────────────────────────────
    _FILLER = {
        "tell", "show", "find", "give", "get", "what", "where", "how",
        "is", "the", "me", "about", "info", "information", "details",
        "more", "some", "a", "an", "and", "or", "for", "in", "on", "at",
        "campus", "located", "location",
    }
    trigger_patterns = [
        # "about Stanford University" — after 'about' or 'for'
        r"(?:about|for)\s+(?:the\s+)?([A-Z][A-Za-z]+(?:\s+(?:of\s+)?[A-Z][A-Za-z]+){0,4})",
        # "where is Harvard" — capital word required right after trigger
        r"(?:where\s+is|location\s+of|address\s+of)\s+(?:the\s+)?([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})",
        # "show me the MIT campus" — only capitals before campus keyword
        r"(?:show\s+me\s+(?:the\s+)?|find\s+(?:the\s+)?)([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})\s+(?:campus|university|college|institute)\b",
        # "Harvard campus" — standalone capitalised noun before campus keyword
        r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})\s+(?:campus|university|college|institute)\b",
        # "Harvard programs" / "MIT location"
        r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})\s+(?:programs?|website|location|address|admissions|ranking)\b",
    ]
    for pat in trigger_patterns:
        m = re.search(pat, query)
        if m:
            words = m.group(1).strip().split()
            # Drop leading/trailing filler (lowercase comparison)
            while words and words[0].lower() in _FILLER:
                words.pop(0)
            while words and words[-1].lower() in _FILLER:
                words.pop()
            candidate = " ".join(words).strip(" ,'s")
            # Must start with capital, be more than 2 chars
            if candidate and len(candidate) > 2 and candidate[0].isupper():
                return candidate

    # ── d) "X State" / "X Tech" / "X Polytechnic" ────────────────────────
    state_tech = re.search(
        r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s+(State|Tech|Polytechnic)\b",
        query
    )
    if state_tech:
        return f"{state_tech.group(1)} {state_tech.group(2)}"

    # ── e) Two+ consecutive Title-Case words (Johns Hopkins, etc.) ────────
    proper = re.search(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", query)
    if proper:
        candidate = proper.group(1).strip()
        words = candidate.split()
        if not all(w in _FILLER for w in words) and len(candidate) > 4:
            return candidate

    return ""


# ── Static cache lookup ───────────────────────────────────────────────────────

def _lookup_static(name: str) -> dict[str, Any] | None:
    """
    Case-insensitive lookup in CAMPUS_DB.
    Tries exact match first, then checks if stored name matches query.
    Uses word-boundary matching to avoid false positives 
    (e.g., "George Washington" shouldn't match "George Mason").
    """
    if not name:
        return None
    lower = name.lower().strip()
    
    # Exact key match (fastest path)
    if lower in CAMPUS_DB:
        return CAMPUS_DB[lower]
    
    # Check if any DB entry's full name matches the query
    # Only match if ALL significant words from the DB name appear in the query
    for key, data in CAMPUS_DB.items():
        db_name_lower = data["name"].lower()
        
        # Exact name match
        if lower == db_name_lower:
            return data
        
        # Check if the query contains the complete university name
        # Split into words and check significant words (ignore common words)
        common_words = {"university", "college", "of", "the", "at"}
        db_words = [w for w in db_name_lower.split() if w not in common_words]
        query_words = set(lower.split())
        
        # All significant words from DB name must be in query
        if db_words and all(word in query_words for word in db_words):
            return data
    
    return None


# ── Dynamic resolution via Wikipedia REST API ─────────────────────────────────

async def _fetch_wikipedia_campus(name: str) -> dict[str, Any] | None:
    """
    Build a campus dict from the Wikipedia Summary REST API.
    Free, no API key, never rate-limits for normal usage.
    Returns None if the university isn't found or the page isn't about a university.
    """
    import urllib.parse

    # Try the name as-is, then with "University" appended
    candidates = [name]
    lower = name.lower()
    if "university" not in lower and "college" not in lower and "institute" not in lower:
        candidates.append(f"{name} University")

    headers = {
        "User-Agent": "portal-survey-agent/2.0 (student-project; educational-use)",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
        for title in candidates:
            slug = urllib.parse.quote(title.replace(" ", "_"))
            url  = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
            try:
                r = await client.get(url)
                if r.status_code != 200:
                    logger.warning("Wikipedia returned %d for %r", r.status_code, title)
                    continue

                wiki = r.json()

                # Make sure the page is actually about an educational institution
                desc    = wiki.get("description", "").lower()
                extract = wiki.get("extract", "")
                edu_terms = ("university", "college", "institute", "school", "academy")
                if not any(t in desc for t in edu_terms):
                    if not any(t in extract.lower() for t in edu_terms):
                        logger.debug("Wikipedia page for %r is not an educational institution, skipping", title)
                        continue

                # Coordinates (Wikipedia provides these directly for most campuses)
                coords = wiki.get("coordinates", {})
                lat = coords.get("lat")
                lng = coords.get("lon")

                # Extract .edu URL from the extract text
                official = _extract_url(extract, name)

                # Parse facts from the extract text
                facts = _parse_facts(extract)

                # Infer university type from the Wikipedia description if regex missed it
                if not facts.get("type") or facts["type"] == "University":
                    if "private" in desc:
                        facts["type"] = "Private university"
                    elif "public" in desc:
                        facts["type"] = "Public university"
                    elif "community college" in desc:
                        facts["type"] = "Community college"
                    elif "technical" in desc or "technology" in desc:
                        facts["type"] = "Technical university"

                # Extract city / state from the Wikipedia description
                # Descriptions look like: "Private research university in Washington, D.C., US"
                city, state = "", ""
                loc_match = re.search(
                    r'\bin\s+([A-Za-z][A-Za-z\s.]+?),\s*([A-Za-z][A-Za-z\s.]+?)(?:,\s*\w+)?$',
                    wiki.get("description", ""),
                )
                if loc_match:
                    city  = loc_match.group(1).strip()
                    state = loc_match.group(2).strip()

                normalised_name = wiki.get("title") or _normalise_name(name)
                summary = _trim_to_sentences(extract, 3)

                campus: dict[str, Any] = {
                    "name": normalised_name,
                    "short_name": _make_short_name(normalised_name),
                    "official_url": official,
                    "admissions_url": f"{official}/admissions" if official else "",
                    "location": {
                        "address": f"{city}, {state}".strip(", ") or f"{normalised_name} campus",
                        "city":  city,
                        "state": state,
                        "lat":   lat,
                        "lng":   lng,
                    },
                    "facts": facts,
                    "search_summary": summary,
                    "maps_embed_url": (
                        f"https://maps.google.com/maps?q={lat},{lng}&output=embed&z=15"
                        if lat else
                        f"https://maps.google.com/maps?q={name.replace(' ', '+')}+university&output=embed"
                    ),
                    "maps_link": (
                        f"https://maps.google.com/?q={lat},{lng}"
                        if lat else
                        f"https://maps.google.com/?q={name.replace(' ', '+')}+university"
                    ),
                }
                logger.info("Wikipedia: resolved %r → %r (lat=%s, lng=%s)", name, normalised_name, lat, lng)
                return campus

            except Exception as exc:
                logger.warning("Wikipedia fetch failed for title %r: %s", title, exc)
                continue

    return None


async def _search_build_campus(name: str, original_query: str) -> dict[str, Any] | None:
    """
    Build a campus dict dynamically.
    Strategy: Wikipedia REST API first (free, reliable, structured coordinates),
    then DuckDuckGo as a fallback.
    """
    # ── Wikipedia (primary) ───────────────────────────────────────────────────
    wiki = await _fetch_wikipedia_campus(name)
    if wiki:
        return wiki

    # ── DuckDuckGo (fallback) ─────────────────────────────────────────────────
    logger.info("Wikipedia returned nothing for %r, trying DuckDuckGo", name)
    try:
        from langchain_community.tools import DuckDuckGoSearchRun

        loop = asyncio.get_event_loop()

        def _ddg(query: str) -> str:
            return DuckDuckGoSearchRun().run(query)[:800]

        loc_snippet, fact_snippet = await asyncio.gather(
            loop.run_in_executor(None, _ddg, f"{name} university campus address location coordinates"),
            loop.run_in_executor(None, _ddg, f"{name} university founded students programs type"),
        )

        location = _parse_location(loc_snippet, name)
        facts    = _parse_facts(fact_snippet)
        official = _extract_url(loc_snippet + " " + fact_snippet, name)

        campus: dict[str, Any] = {
            "name": _normalise_name(name),
            "short_name": _make_short_name(name),
            "official_url": official,
            "admissions_url": f"{official}/admissions" if official else "",
            "location": location,
            "facts": facts,
            "search_summary": _trim_to_sentences(loc_snippet, 3),
            "maps_embed_url": (
                f"https://maps.google.com/maps?q={location['lat']},{location['lng']}&output=embed&z=15"
                if location["lat"] else
                f"https://maps.google.com/maps?q={name.replace(' ', '+')}+university&output=embed"
            ),
            "maps_link": (
                f"https://maps.google.com/?q={location['lat']},{location['lng']}"
                if location["lat"] else
                f"https://maps.google.com/?q={name.replace(' ', '+')}+university"
            ),
        }
        logger.info("DuckDuckGo: resolved %r", name)
        return campus

    except Exception as exc:
        logger.warning("DuckDuckGo search also failed for %r: %s: %s", name, type(exc).__name__, exc)
        return None


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _parse_location(snippet: str, name: str) -> dict[str, Any]:
    """Extract lat/lng and address from a search snippet."""
    lat, lng = None, None

    # Look for decimal coordinates in the snippet
    coord_match = re.search(
        r'(-?\d{1,3}\.\d{3,})\s*[,°]\s*(-?\d{1,3}\.\d{3,})',
        snippet,
    )
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lng = float(coord_match.group(2))
            # Sanity check — valid world coordinates
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                lat, lng = None, None
        except ValueError:
            lat, lng = None, None

    # Extract address — look for "N Street, City, State ZIP" patterns
    address = ""
    addr_match = re.search(
        r'\d+\s+[A-Za-z0-9\s.]+(?:St|Ave|Blvd|Dr|Rd|Way|Lane|Ln|Pkwy)[.,]?\s*'
        r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}',
        snippet,
        re.IGNORECASE,
    )
    if addr_match:
        address = addr_match.group(0).strip()

    # Extract city/state
    city, state = "", ""
    city_match = re.search(r'(?:located in|campus in|in)\s+([A-Za-z\s]+),\s*([A-Z]{2})', snippet, re.IGNORECASE)
    if city_match:
        city  = city_match.group(1).strip()
        state = city_match.group(2).strip()

    return {
        "address": address or f"{name} campus",
        "city":    city,
        "state":   state,
        "lat":     lat,
        "lng":     lng,
    }


def _parse_facts(snippet: str) -> dict[str, str]:
    """Extract founded year, student count, and type from a search snippet."""
    facts: dict[str, str] = {
        "founded":  "",
        "students": "",
        "programs": "",
        "type":     "University",
        "nickname": "",
    }

    # Founded year
    year = re.search(r'(?:founded|established|chartered)\s+(?:in\s+)?(\d{4})', snippet, re.IGNORECASE)
    if year:
        facts["founded"] = year.group(1)

    # Student count
    students = re.search(
        r'([\d,]+\+?)\s+(?:students|undergraduate|enrollment)',
        snippet, re.IGNORECASE
    )
    if students:
        facts["students"] = students.group(1) + " students"

    # University type
    for t in ("public research", "private research", "public", "private",
              "liberal arts", "community college", "technical"):
        if t in snippet.lower():
            facts["type"] = t.title() + " university"
            break

    return facts


def _extract_url(snippet: str, name: str) -> str:
    """Try to find the official .edu URL in the snippet. Returns '' if not found."""
    edu_match = re.search(r'https?://(?:www\.)?[\w.-]+\.edu\b', snippet)
    if edu_match:
        return edu_match.group(0).rstrip("/")
    return ""


def _normalise_name(name: str) -> str:
    """Ensure 'University' is appended if not already present."""
    lower = name.lower()
    if "university" in lower or "college" in lower or "institute" in lower:
        return name.title()
    return f"{name.title()} University"


def _make_short_name(name: str) -> str:
    """MIT → MIT, Stanford University → Stanford."""
    # If already an abbreviation (all caps, short)
    if name.isupper() and len(name) <= 5:
        return name
    # Remove "University / College" suffix
    short = re.sub(r'\b(?:University|College|Institute|of|the)\b', '', name, flags=re.IGNORECASE)
    return short.strip().title()


def _trim_to_sentences(text: str, n: int) -> str:
    """Return the first n sentences from a snippet."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:n]).strip()


# ── Official page meta (unchanged) ───────────────────────────────────────────

async def fetch_official_page_meta(url: str) -> dict[str, str]:
    """
    Fetch <title> and <meta description> from any URL.
    Reads only the first 6 KB so it is fast even for slow sites.
    """
    try:
        async with httpx.AsyncClient(timeout=8, trust_env=False) as client:
            async with client.stream("GET", url) as r:
                html = b""
                async for chunk in r.aiter_bytes(chunk_size=1024):
                    html += chunk
                    if b"</head>" in html or len(html) > 6000:
                        break

        text = html.decode("utf-8", errors="ignore")
        title = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        desc  = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
            text, re.IGNORECASE,
        )
        return {
            "title":       title.group(1).strip() if title else "",
            "description": desc.group(1).strip()  if desc  else "",
        }
    except Exception:
        return {"title": "", "description": ""}



async def resolve_campus(query: str) -> dict[str, Any] | None:
    """
    Main entry point — given any user query, return a campus dict or None.

    Returns None when no university could be identified or resolved, so the
    caller (CampusInfoAgent) can respond with an appropriate message instead
    of showing fake data.

    Strategy:
    1. Extract the university name from the query text
    2. Check CAMPUS_DB (instant, zero cost)
    3. If not found, resolve dynamically via Wikipedia REST API → DuckDuckGo
    4. Return None if nothing is found (not a university query)
    """
    university_name = extract_university_name(query)
    logger.info("resolve_campus: extracted university name %r from query %r", university_name, query)

    if not university_name:
        logger.info("resolve_campus: no university name found in query")
        return None

    # Static cache first
    cached = _lookup_static(university_name)
    if cached:
        logger.info("resolve_campus: static cache hit for %r", university_name)
        return cached

    # Dynamic resolution (Wikipedia → DuckDuckGo)
    dynamic = await _search_build_campus(university_name, query)
    if dynamic:
        return dynamic

    logger.warning("resolve_campus: could not resolve %r via any source", university_name)
    return None


async def web_search_campus(query: str, campus_name: str) -> str:
    """
    General-purpose campus web search.
    Returns a short plain-text snippet (~3 sentences).
    """
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        searcher = DuckDuckGoSearchRun()
        result: str = searcher.run(f"{campus_name} {query}")
        return _trim_to_sentences(result, 3)
    except Exception:
        return ""