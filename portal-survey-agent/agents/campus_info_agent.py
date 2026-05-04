"""
agents/campus_info_agent.py
-----------------------------
Answers campus questions for ANY university — not just GMU.

WHAT CHANGED FROM v1
---------------------
v1: always called get_campus_static(DEFAULT_CAMPUS) → always returned GMU.

v2: calls resolve_campus(query) which:
  1. Extracts the university name from the user's query
  2. Checks CAMPUS_DB first (instant, zero cost)
  3. Falls back to DuckDuckGo search for unknown universities
  4. Returns a normalised dict in the same shape as a CAMPUS_DB entry

Everything downstream (result builders, ui_hints, chips) is unchanged
because the dict shape is identical.

EXAMPLE QUERIES THAT NOW WORK
------------------------------
- "Where is MIT located?"
- "Tell me about Stanford University"
- "What programs does UCLA offer?"
- "Show me the Carnegie Mellon campus"
- "NYU official website"
- "Where is the Johns Hopkins campus?"
- "Tell me about George Mason University"   ← still works via static cache
"""
from __future__ import annotations

from typing import Any

from shared.state import AgentState
from shared.tools.campus_tool import (
    extract_university_name,
    fetch_official_page_meta,
    resolve_campus,
    web_search_campus,
)


class CampusInfoAgent:
    async def run(self, state: AgentState) -> AgentState:
        query = state.get("user_query", "")

        # ── Step 1: resolve campus (static cache → Wikipedia → DuckDuckGo) ──
        campus = await resolve_campus(query)

        # ── Step 2: not a university query ────────────────────────────────────
        if campus is None:
            state["campus_result"] = {
                "ok": False,
                "query_type": "not_found",
                "name": "",
                "summary": (
                    "I can only look up information about universities and colleges. "
                    "Try asking about a specific university — for example: "
                    "\"Where is George Mason University?\" or \"Tell me about MIT.\""
                ),
                "ui_hints": {
                    "show_map": False,
                    "show_info_chips": False,
                    "show_link_card": False,
                    "quick_actions": [
                        {"label": "About GMU", "prompt": "Tell me about George Mason University"},
                        {"label": "GMU location", "prompt": "Where is George Mason University?"},
                        {"label": "GMU website", "prompt": "What is the official GMU website?"},
                    ],
                },
            }
            return state

        # ── Step 3: classify what kind of campus info is needed ───────────────
        query_type = self._classify_query(query.lower())

        # ── Step 4: build the result ──────────────────────────────────────────
        try:
            if query_type == "location":
                result = self._build_location_result(campus, query)
            elif query_type == "official_site":
                result = await self._build_site_result(campus)
            else:
                result = await self._build_search_result(campus, query)
        except Exception as exc:
            name = campus.get("name", "the campus")
            result = {
                "ok": True,
                "query_type": "error_fallback",
                "name": name,
                "summary": (
                    f"I found information about {name} but encountered an error "
                    f"building the full response: {exc}."
                ),
                "ui_hints": {
                    "show_map": False,
                    "show_info_chips": False,
                    "show_link_card": bool(campus.get("official_url")),
                    "link_card": {
                        "title": name,
                        "url": campus.get("official_url", ""),
                        "description": "Official university website",
                    },
                    "quick_actions": [],
                },
            }

        state["campus_result"] = result
        return state

    # ── Query type classification ─────────────────────────────────────────────

    def _classify_query(self, query: str) -> str:
        """
        Decide what kind of campus info the user wants.
        Checks word membership, not substring — avoids false positives.
        """
        words = set(query.split())
        location_words = {
            "location", "map", "where", "address", "directions",
            "located", "commute", "metro", "transit", "get", "there",
        }
        site_words = {
            "official", "website", "site", "url", "portal", "web", "link",
        }
        if words & location_words:
            return "location"
        if words & site_words:
            return "official_site"
        return "general"

    # ── Result builders ───────────────────────────────────────────────────────

    def _build_location_result(
        self, campus: dict[str, Any], original_query: str
    ) -> dict[str, Any]:
        loc   = campus.get("location", {})
        name  = campus.get("name", "This university")
        short = campus.get("short_name", name)

        # Build address line — use what we have
        addr  = loc.get("address") or f"{name} campus"
        city  = loc.get("city", "")
        state = loc.get("state", "")
        loc_desc = f"{city}, {state}" if city and state else addr

        summary = f"{name} is located at {addr}."
        if city and state:
            facts = campus.get("facts", {})
            utype = facts.get("type", "university")
            summary += f" It is a {utype} in {city}, {state}."

        # If we got coords from search, show the embed; otherwise use text search
        has_coords = bool(loc.get("lat") and loc.get("lng"))

        return {
            "ok": True,
            "query_type": "location",
            "name": name,
            "summary": summary,
            "ui_hints": {
                "show_map": True,
                "map": {
                    "lat":       loc.get("lat", 0),
                    "lng":       loc.get("lng", 0),
                    "label":     name,
                    "address":   addr,
                    "embed_url": campus.get("maps_embed_url", ""),
                    "maps_link": campus.get("maps_link", f"https://maps.google.com/?q={name.replace(' ', '+')}"),
                },
                "show_info_chips": True,
                "chips": self._build_chips(campus),
                "show_link_card": bool(campus.get("official_url")),
                "link_card": {
                    "title":       name,
                    "url":         campus.get("official_url", ""),
                    "description": "Official university portal",
                },
                "quick_actions": [
                    {"label": f"{short} programs",   "prompt": f"What programs does {name} offer?"},
                    {"label": f"{short} website",    "prompt": f"What is the official {name} website?"},
                    {"label": "Student feedback",    "prompt": "Summarize what students feel about campus life"},
                ],
            },
        }

    async def _build_site_result(self, campus: dict[str, Any]) -> dict[str, Any]:
        name = campus.get("name", "This university")
        url  = campus.get("official_url", "")
        short = campus.get("short_name", name)

        # Try fetching live meta from the official page
        meta = await fetch_official_page_meta(url) if url else {}
        description = (
            meta.get("description")
            or campus.get("search_summary", "")
            or f"Official portal for {name}"
        )

        return {
            "ok": True,
            "query_type": "official_site",
            "name": name,
            "summary": (
                f"The official {name} website is {url}. {description}"
                if url else
                f"I could not determine the official website for {name}."
            ),
            "ui_hints": {
                "show_map": False,
                "show_info_chips": True,
                "chips": self._build_chips(campus),
                "show_link_card": bool(url),
                "link_card": {
                    "title":          name,
                    "url":            url,
                    "description":    description[:120],
                    "admissions_url": campus.get("admissions_url", ""),
                },
                "quick_actions": [
                    {"label": f"{short} location",  "prompt": f"Where is {name} located?"},
                    {"label": f"{short} programs",  "prompt": f"What programs does {name} offer?"},
                    {"label": "Student feedback",   "prompt": "Summarize what students feel about campus life"},
                ],
            },
        }

    async def _build_search_result(
        self, campus: dict[str, Any], query: str
    ) -> dict[str, Any]:
        name  = campus.get("name", "This university")
        short = campus.get("short_name", name)

        # Prefer a live search snippet; fall back to the one we got during resolve
        snippet = await web_search_campus(query, name)
        if not snippet:
            snippet = campus.get("search_summary", "")

        facts = campus.get("facts", {})
        if not snippet:
            loc   = campus.get("location", {})
            city  = loc.get("city", "")
            state = loc.get("state", "")
            where = f"in {city}, {state}" if city and state else ""
            snippet = (
                f"{name} is a {facts.get('type', 'university')} {where}."
                + (f" Founded {facts['founded']}." if facts.get('founded') else "")
                + (f" Enrollment: {facts['students']}." if facts.get('students') else "")
            )

        return {
            "ok": True,
            "query_type": "general",
            "name": name,
            "summary": snippet,
            "ui_hints": {
                "show_map": False,
                "show_info_chips": True,
                "chips": self._build_chips(campus),
                "show_link_card": bool(campus.get("official_url")),
                "link_card": {
                    "title":       name,
                    "url":         campus.get("official_url", ""),
                    "description": f"Official portal — {facts.get('programs', 'programs and admissions')}",
                },
                "quick_actions": [
                    {"label": f"{short} location", "prompt": f"Where is {name} located?"},
                    {"label": f"{short} website",  "prompt": f"What is the official {name} website?"},
                    {"label": "Student feedback",  "prompt": "Summarize what students feel about campus life"},
                ],
            },
        }

    # ── Shared helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _build_chips(campus: dict[str, Any]) -> list[dict[str, str]]:
        """Build info chips from whatever facts we have — static or dynamically found."""
        facts = campus.get("facts", {})
        loc   = campus.get("location", {})
        chips = []

        city  = loc.get("city", "")
        state = loc.get("state", "")
        if city or state:
            chips.append({"label": "Location", "value": f"{city}, {state}".strip(", ")})

        if facts.get("founded"):
            chips.append({"label": "Founded",  "value": facts["founded"]})
        if facts.get("students"):
            chips.append({"label": "Students", "value": facts["students"]})
        if facts.get("programs"):
            chips.append({"label": "Programs", "value": facts["programs"]})
        if facts.get("type"):
            chips.append({"label": "Type",     "value": facts["type"]})

        # If we got nothing from facts, add the URL as a chip
        if not chips and campus.get("official_url"):
            chips.append({"label": "Website", "value": campus["official_url"]})

        return chips
# """
# agents/campus_info_agent.py
# -----------------------------
# Answers real-world questions about the campus:
#   - Location and address
#   - Map coordinates + Google Maps link
#   - Official website info
#   - General info (programs, rankings, events) via web search

# HOW IT DECIDES WHAT TO DO
# --------------------------
# _classify_query() checks the user's message for keyword groups:

#   "location / map / where / address / directions"  --> get_location
#   "official / website / site / url / portal"       --> get_official_site
#   anything else                                    --> web_search

# All three paths converge at _synthesize() which packages the result
# into the "campus_result" key that the supervisor reads.

# THE ui_hints KEY
# ----------------
# campus_result["ui_hints"] is a nested dict the React component reads
# to decide WHAT to render beyond plain text:
#   - show_map: bool         → renders a Google Maps embed iframe
#   - show_info_chips: bool  → renders fact chips (founded, students, …)
#   - show_link_card: bool   → renders a clickable site card with URL
#   - quick_actions: list    → renders suggestion buttons below the bubble
# """
# from __future__ import annotations

# from typing import Any

# from shared.state import AgentState
# from shared.tools.campus_tool import (
#     CAMPUS_DB,
#     DEFAULT_CAMPUS,
#     fetch_official_page_meta,
#     get_campus_static,
#     web_search_campus,
# )


# class CampusInfoAgent:
#     async def run(self, state: AgentState) -> AgentState:
#         query = state.get("user_query", "")
#         campus = get_campus_static(DEFAULT_CAMPUS)
#         query_type = self._classify_query(query.lower())

#         if query_type == "location":
#             result = self._build_location_result(campus)
#         elif query_type == "official_site":
#             result = await self._build_site_result(campus)
#         else:
#             result = await self._build_search_result(campus, query)

#         state["campus_result"] = result
#         return state

#     # ── query classification ──────────────────────────────────────────────────

#     def _classify_query(self, query: str) -> str:
#         location_words = {"location", "map", "where", "address", "directions", "get there", "metro", "commute"}
#         site_words = {"official", "website", "site", "url", "portal", "gmu.edu", "web"}
#         if any(w in query for w in location_words):
#             return "location"
#         if any(w in query for w in site_words):
#             return "official_site"
#         return "general"

#     # ── result builders ───────────────────────────────────────────────────────

#     def _build_location_result(self, campus: dict[str, Any]) -> dict[str, Any]:
#         loc = campus["location"]
#         return {
#             "ok": True,
#             "query_type": "location",
#             "name": campus["name"],
#             "summary": (
#                 f"{campus['name']} is located at {loc['address']}. "
#                 f"It is a {campus['facts']['type']} in {loc['city']}, {loc['state']}."
#             ),
#             "ui_hints": {
#                 "show_map": True,
#                 "map": {
#                     "lat": loc["lat"],
#                     "lng": loc["lng"],
#                     "label": campus["name"],
#                     "address": loc["address"],
#                     "embed_url": campus["maps_embed_url"],
#                     "maps_link": campus["maps_link"],
#                 },
#                 "show_info_chips": True,
#                 "chips": self._build_chips(campus),
#                 "show_link_card": True,
#                 "link_card": {
#                     "title": campus["name"],
#                     "url": campus["official_url"],
#                     "description": "Official university portal",
#                 },
#                 "quick_actions": [
#                     {"label": "CS programs", "prompt": f"What CS programs does {campus['short_name']} offer?"},
#                     {"label": "Student sentiment", "prompt": f"Summarize what students feel about {campus['short_name']}"},
#                     {"label": "Survey data", "prompt": "Show me all survey results"},
#                 ],
#             },
#         }

#     async def _build_site_result(self, campus: dict[str, Any]) -> dict[str, Any]:
#         meta = await fetch_official_page_meta(campus["official_url"])
#         description = meta.get("description") or f"Official portal for {campus['name']}"
#         return {
#             "ok": True,
#             "query_type": "official_site",
#             "name": campus["name"],
#             "summary": (
#                 f"The official {campus['name']} website is {campus['official_url']}. "
#                 f"{description}"
#             ),
#             "ui_hints": {
#                 "show_map": False,
#                 "show_info_chips": True,
#                 "chips": self._build_chips(campus),
#                 "show_link_card": True,
#                 "link_card": {
#                     "title": campus["name"],
#                     "url": campus["official_url"],
#                     "description": description,
#                     "admissions_url": campus["admissions_url"],
#                 },
#                 "quick_actions": [
#                     {"label": "Campus location", "prompt": f"Where is {campus['short_name']} located?"},
#                     {"label": "Student feedback", "prompt": "Summarize student survey sentiment"},
#                     {"label": "Survey stats", "prompt": "Show analytics overview of all surveys"},
#                 ],
#             },
#         }

#     async def _build_search_result(
#         self, campus: dict[str, Any], query: str
#     ) -> dict[str, Any]:
#         snippet = await web_search_campus(query, campus["name"])
#         summary = snippet if snippet else (
#             f"{campus['name']} is a {campus['facts']['type']} in "
#             f"{campus['location']['city']}, {campus['location']['state']} "
#             f"with {campus['facts']['students']} students and {campus['facts']['programs']}."
#         )
#         return {
#             "ok": True,
#             "query_type": "general",
#             "name": campus["name"],
#             "summary": summary,
#             "ui_hints": {
#                 "show_map": False,
#                 "show_info_chips": True,
#                 "chips": self._build_chips(campus),
#                 "show_link_card": True,
#                 "link_card": {
#                     "title": campus["name"],
#                     "url": campus["official_url"],
#                     "description": f"Official portal — {campus['facts']['programs']}",
#                 },
#                 "quick_actions": [
#                     {"label": "Campus location", "prompt": f"Where is {campus['short_name']}?"},
#                     {"label": "Official site", "prompt": f"Show me the {campus['short_name']} official website"},
#                     {"label": "Student sentiment", "prompt": "What do students feel about campus life?"},
#                 ],
#             },
#         }

#     # ── shared helpers ────────────────────────────────────────────────────────

#     @staticmethod
#     def _build_chips(campus: dict[str, Any]) -> list[dict[str, str]]:
#         facts = campus["facts"]
#         loc = campus["location"]
#         return [
#             {"label": "Location", "value": f"{loc['city']}, {loc['state']}"},
#             {"label": "Founded", "value": facts["founded"]},
#             {"label": "Students", "value": facts["students"]},
#             {"label": "Programs", "value": facts["programs"]},
#             {"label": "Type", "value": facts["type"]},
#         ]