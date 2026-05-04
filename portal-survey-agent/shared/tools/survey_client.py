"""
shared/tools/survey_client.py
------------------------------
Async wrapper around portal-survey-api REST endpoints.
Every public method returns {"ok": bool, ...} so callers
never inspect HTTP status codes directly.

HOW IT WORKS
------------
call(tool_name, arguments) is the single entry point.
It matches tool_name to an HTTP call and normalises the
response into a consistent shape.  The CRUD agent calls
this; the analytics agent also calls list_surveys through
this same client so there is exactly one place that
knows about API URLs.
"""
from __future__ import annotations

from typing import Any

import httpx

from config import settings


class SurveyToolClient:
    def __init__(self) -> None:
        self.api_base = settings.API_BASE_URL.rstrip("/")

    # ── single public entry-point ────────────────────────────────

    async def call(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        arguments = arguments or {}
        try:
            return await self._dispatch(tool_name, arguments)
        except Exception as exc:
            return {
                "ok": False,
                "message": (
                    f"Tool '{tool_name}' failed. "
                    f"Is the API running at {self.api_base}? Detail: {exc}"
                ),
            }

    # ── internal dispatcher ──────────────────────────────────────

    async def _dispatch(
        self, tool_name: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20, trust_env=False) as client:
            if tool_name == "create_survey":
                r = await client.post(
                    f"{self.api_base}/api/surveys", json=args["payload"]
                )
                return self._wrap(r, "survey")

            if tool_name == "list_surveys":
                r = await client.get(f"{self.api_base}/api/surveys")
                return self._wrap(r)

            if tool_name == "get_survey_by_id":
                r = await client.get(
                    f"{self.api_base}/api/surveys/{args['survey_id']}"
                )
                return self._wrap(r, "survey")

            if tool_name == "search_surveys":
                r = await client.get(f"{self.api_base}/api/surveys")
                payload = self._wrap(r)
                filtered = self._filter(payload.get("surveys", []), args)
                return {"ok": True, "total": len(filtered), "surveys": filtered}

            if tool_name == "update_survey":
                r = await client.put(
                    f"{self.api_base}/api/surveys/{args['survey_id']}",
                    json=args["changes"],
                )
                return self._wrap(r, "survey")

            if tool_name == "delete_survey":
                r = await client.delete(
                    f"{self.api_base}/api/surveys/{args['survey_id']}"
                )
                return self._wrap(r)

        return {"ok": False, "message": f"Unknown tool: {tool_name}"}

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _wrap(
        response: httpx.Response, key: str | None = None
    ) -> dict[str, Any]:
        """Turn an httpx response into {"ok": bool, ...}."""
        if response.status_code >= 400:
            return {
                "ok": False,
                "message": response.text,
                "status_code": response.status_code,
            }
        data = response.json()
        if key and key not in data:
            # API returned the object directly (not wrapped)
            return {"ok": True, key: data}
        return {"ok": True, **data}

    @staticmethod
    def _filter(
        surveys: list[dict[str, Any]], args: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Client-side filter for search_surveys.

        Match rules:
        - first_name / last_name: flexible matching
          * If both provided: check if ALL search words appear ANYWHERE in the full name
          * If only one provided: substring match on that field
        - interest_source: case-insensitive exact match
        - recommendation: case-insensitive EXACT match
          ("Likely" must NOT match "Very Likely" or "Unlikely")
        - liked_most: exact item match in the list (case-insensitive)
        """
        def matches(s: dict[str, Any]) -> bool:
            # Name filtering — flexible multi-word support
            search_first = args.get("first_name", "").lower()
            search_last = args.get("last_name", "").lower()
            
            if search_first or search_last:
                # Build full name from survey
                survey_first = str(s.get("first_name", "")).lower()
                survey_last = str(s.get("last_name", "")).lower()
                survey_full_name = f"{survey_first} {survey_last}".strip()
                
                # Build search term
                search_full = f"{search_first} {search_last}".strip()
                
                # Check if ALL words from search appear in the survey's full name
                search_words = search_full.split()
                for word in search_words:
                    if word not in survey_full_name:
                        return False

            # Interest source — exact match
            interest = args.get("interest_source")
            if interest and interest.lower() != str(s.get("interest_source", "")).lower():
                return False

            # Recommendation — exact match (NOT substring)
            # "Likely" must not match "Very Likely" or "Unlikely"
            rec = args.get("recommendation")
            if rec and rec.lower() != str(s.get("recommendation", "")).lower():
                return False

            # liked_most — must appear as an exact item in the list
            liked = args.get("liked_most")
            if liked:
                values = [item.lower() for item in s.get("liked_most", [])]
                if liked.lower() not in values:
                    return False

            return True

        return [s for s in surveys if matches(s)]