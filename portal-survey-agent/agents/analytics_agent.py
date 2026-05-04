"""
agents/analytics_agent.py
--------------------------
Answers statistical questions about survey data — no LLM needed.

WHAT THIS AGENT DOES
--------------------
It fetches ALL surveys from the API once, then runs Python
aggregations against that list. The result is a structured dict
that the supervisor uses to build a response and ui_hints.

EXAMPLE QUERIES IT HANDLES
---------------------------
- "How many surveys do we have?"
- "How many students liked dorm rooms?"
- "What is the most common recommendation?"
- "Show me a breakdown of interest sources"
- "How many surveys came from internet vs friends?"
- "Count surveys where recommendation is Likely"

HOW TO ADD A NEW METRIC
------------------------
1. Add a keyword pattern to _detect_query_type()
2. Add a matching branch in _compute() that reads self.surveys
3. Return {"metric": "...", "value": ..., "detail": {...}}
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from shared.state import AgentState
from shared.tools.survey_client import SurveyToolClient


class AnalyticsAgent:
    def __init__(self) -> None:
        self.client = SurveyToolClient()

    async def run(self, state: AgentState) -> AgentState:
        """
        Entry point. Fetches surveys, computes the right metric,
        writes result into state["analytics_result"].
        """
        query = state.get("user_query", "").lower()

        # Step 1 — fetch all surveys (one API call, always)
        raw = await self.client.call("list_surveys")
        if not raw.get("ok"):
            state["analytics_result"] = {
                "ok": False,
                "message": "Could not fetch survey data from the API.",
            }
            return state

        surveys: list[dict[str, Any]] = raw.get("surveys", [])
        total = len(surveys)

        if total == 0:
            state["analytics_result"] = {
                "ok": True,
                "summary": "There are no surveys in the system yet.",
                "total": 0,
                "charts": [],
            }
            return state

        # Step 2 — detect what kind of analytics to run
        query_type = self._detect_query_type(query)

        # Step 3 — compute and store
        state["analytics_result"] = self._compute(query_type, surveys, total, query)
        return state

    # ── query type detection ──────────────────────────────────────────────────

    def _detect_query_type(self, query: str) -> str:
        """
        Map the user query to one of our supported analytics types.
        Order matters — check most specific first.
        """
        # Check for specific counting/filtering questions FIRST
        # These take priority over generic breakdown requests
        if any(w in query for w in ["how many", "count", "number of"]):
            return "total_count"
        
        # Then check for specific breakdowns
        if any(w in query for w in ["recommendation", "recommend", "likely", "unlikely"]):
            return "recommendation_breakdown"
        if any(w in query for w in ["interest", "internet", "friends", "television", "other", "source"]):
            return "interest_breakdown"
        if any(w in query for w in ["liked", "like most", "dorm", "atmosphere", "sports", "campus", "location", "students"]):
            return "liked_breakdown"
        
        # Default: give an overview of all metrics
        return "overview"

    # ── computation ───────────────────────────────────────────────────────────

    def _compute(
        self,
        query_type: str,
        surveys: list[dict[str, Any]],
        total: int,
        raw_query: str,
    ) -> dict[str, Any]:
        """Dispatch to the right aggregation function."""
        if query_type == "total_count":
            return self._count(surveys, total, raw_query)
        if query_type == "liked_breakdown":
            return self._liked_breakdown(surveys, total, raw_query)
        if query_type == "recommendation_breakdown":
            return self._recommendation_breakdown(surveys, total)
        if query_type == "interest_breakdown":
            return self._interest_breakdown(surveys, total)
        # overview — return everything
        return self._overview(surveys, total)

    def _count(
        self, surveys: list[dict[str, Any]], total: int, query: str
    ) -> dict[str, Any]:
        """
        Answer "how many" questions.
        Detects filter keywords and counts matching surveys.
        """
        # Check if query filters by liked item
        liked_keywords = {
            "dorm": "dorm_rooms", "atmosphere": "atmosphere",
            "sports": "sports", "campus": "campus",
            "location": "location", "students": "students",
        }
        for kw, value in liked_keywords.items():
            if kw in query:
                matching = [
                    s for s in surveys
                    if value in [item.lower() for item in s.get("liked_most", [])]
                ]
                return {
                    "ok": True,
                    "summary": f"{len(matching)} out of {total} students liked {value.replace('_', ' ')}.",
                    "total": total,
                    "filtered_count": len(matching),
                    "filter": f"liked_most = {value}",
                    "charts": [self._bar_chart("Liked filter", {value: len(matching), "others": total - len(matching)})],
                }

        # Recommendation filter
        for rec in ("Very Likely", "Likely", "Unlikely"):
            if rec.lower() in query:
                matching = [s for s in surveys if s.get("recommendation") == rec]
                return {
                    "ok": True,
                    "summary": f"{len(matching)} students have recommendation '{rec}'.",
                    "total": total,
                    "filtered_count": len(matching),
                    "charts": [],
                }

        # Plain total count
        return {
            "ok": True,
            "summary": f"There are {total} surveys in the system.",
            "total": total,
            "charts": [],
        }

    def _liked_breakdown(
        self, surveys: list[dict[str, Any]], total: int, query: str
    ) -> dict[str, Any]:
        """Count how many students liked each campus feature."""
        counter: Counter = Counter()
        for s in surveys:
            for item in s.get("liked_most", []):
                counter[item.lower()] += 1
        most_common = counter.most_common(1)
        top = most_common[0][0] if most_common else "N/A"
        return {
            "ok": True,
            "summary": f"Most liked feature: {top.replace('_', ' ')} ({counter[top]} students). Breakdown across {total} surveys.",
            "total": total,
            "breakdown": dict(counter),
            "charts": [self._bar_chart("What students liked most", dict(counter))],
        }

    def _recommendation_breakdown(
        self, surveys: list[dict[str, Any]], total: int
    ) -> dict[str, Any]:
        """Count Very Likely / Likely / Unlikely."""
        counter: Counter = Counter(s.get("recommendation", "Unknown") for s in surveys)
        pct = {k: round(v / total * 100) for k, v in counter.items()}
        return {
            "ok": True,
            "summary": (
                f"Recommendation breakdown across {total} surveys: "
                + ", ".join(f"{k} {v}%" for k, v in pct.items())
            ),
            "total": total,
            "breakdown": dict(counter),
            "percentages": pct,
            "charts": [self._bar_chart("Recommendation likelihood", dict(counter))],
        }

    def _interest_breakdown(
        self, surveys: list[dict[str, Any]], total: int
    ) -> dict[str, Any]:
        """Count interest sources (friends, internet, television, other)."""
        counter: Counter = Counter(s.get("interest_source", "unknown") for s in surveys)
        return {
            "ok": True,
            "summary": f"Interest sources across {total} surveys: "
            + ", ".join(f"{k} ({v})" for k, v in counter.most_common()),
            "total": total,
            "breakdown": dict(counter),
            "charts": [self._bar_chart("How students heard about us", dict(counter))],
        }

    def _overview(
        self, surveys: list[dict[str, Any]], total: int
    ) -> dict[str, Any]:
        """Full overview: all three breakdowns in one response."""
        liked_counter: Counter = Counter()
        for s in surveys:
            for item in s.get("liked_most", []):
                liked_counter[item.lower()] += 1
        rec_counter = Counter(s.get("recommendation", "Unknown") for s in surveys)
        src_counter = Counter(s.get("interest_source", "unknown") for s in surveys)

        top_liked = liked_counter.most_common(1)
        top_liked_label = top_liked[0][0].replace("_", " ") if top_liked else "N/A"

        return {
            "ok": True,
            "summary": (
                f"Overview of {total} surveys: "
                f"Most liked feature is {top_liked_label}. "
                f"Top recommendation: {rec_counter.most_common(1)[0][0] if rec_counter else 'N/A'}. "
                f"Top interest source: {src_counter.most_common(1)[0][0] if src_counter else 'N/A'}."
            ),
            "total": total,
            "liked_breakdown": dict(liked_counter),
            "recommendation_breakdown": dict(rec_counter),
            "interest_breakdown": dict(src_counter),
            "charts": [
                self._bar_chart("What students liked most", dict(liked_counter)),
                self._bar_chart("Recommendation likelihood", dict(rec_counter)),
                self._bar_chart("Interest sources", dict(src_counter)),
            ],
        }

    # ── chart data builder ────────────────────────────────────────────────────

    @staticmethod
    def _bar_chart(title: str, data: dict[str, int]) -> dict[str, Any]:
        """
        Return a chart-ready data structure.
        The React UI reads this to render a bar chart via recharts.
        Format: {"type": "bar", "title": "...", "data": [{"label": "x", "value": n}]}
        """
        return {
            "type": "bar",
            "title": title,
            "data": [
                {"label": k.replace("_", " ").title(), "value": v}
                for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)
            ],
        }