"""
agents/crud_agent.py
---------------------
Your original single-agent (graph.py) refactored as a sub-agent.

WHAT CHANGED FROM YOUR ORIGINAL graph.py
-----------------------------------------
1. Class renamed CrudAgent (was SurveyAgent).
2. run() now accepts state dict directly instead of building it internally.
   The supervisor passes its shared AgentState straight in.
3. Result is written to state["crud_result"] so the supervisor can read it.
4. All helper functions (_extract_survey_fields, etc.) are unchanged — they
   live at the bottom of this file exactly as before.

WHAT STAYS IDENTICAL
--------------------
- The 4-node LangGraph (create/read/update/delete branch + execute + response)
- SurveyDraft validation
- The confirmation flow (pending_action / session["confirmation"])
- All regex field extraction logic
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from config import settings
from shared.state import AgentState
from shared.tools.survey_client import SurveyToolClient

# ── Field metadata ────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "first_name", "last_name", "street_address", "city", "state",
    "zip_code", "telephone", "email", "date_of_survey",
    "liked_most", "interest_source", "recommendation",
]

FIELD_LABELS = {
    "first_name": "first name",
    "last_name": "last name",
    "street_address": "street address",
    "city": "city",
    "state": "state",
    "zip_code": "zip code",
    "telephone": "telephone",
    "email": "email",
    "date_of_survey": "survey date, for example today or 2026-04-22",
    "liked_most": "what they liked most",
    "interest_source": "interest source",
    "recommendation": "recommendation: Very Likely, Likely, or Unlikely",
}

LIKED_ALIASES = {
    "students": "students", "location": "location", "campus": "campus",
    "atmosphere": "atmosphere", "dorm": "dorm_rooms", "dorms": "dorm_rooms",
    "dorm rooms": "dorm_rooms", "sports": "sports",
}

INTEREST_OPTIONS = {"friends", "television", "internet", "other"}

RECOMMENDATION_ALIASES = {
    "very likely": "Very Likely", "likely": "Likely", "unlikely": "Unlikely",
    "yes": "Likely", "recommend": "Likely", "would recommend": "Likely",
    "no": "Unlikely", "not recommend": "Unlikely",
}


# ── SurveyDraft model ─────────────────────────────────────────────────────────

class SurveyDraft(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    telephone: str | None = None
    email: str | None = None
    date_of_survey: str | None = None
    liked_most: list[str] = Field(default_factory=list)
    interest_source: str | None = None
    recommendation: str | None = None
    raffle: str | None = None
    comments: str | None = None

    def as_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


# ── Agent ─────────────────────────────────────────────────────────────────────

class CrudAgent:
    """
    Handles all survey CRUD operations via natural language.
    Called by the supervisor as a sub-graph.
    """

    def __init__(self) -> None:
        self.tools = SurveyToolClient()
        self.graph = self._build_graph()
        self._multiple_matches: list[dict[str, Any]] = []

    async def run(self, state: AgentState) -> AgentState:
        """Entry point called by the supervisor dispatch node."""
        result = await self.graph.ainvoke(state)
        # Write result into the shared state key the supervisor reads
        state["crud_result"] = {
            "response": result.get("response", ""),
            "requires_confirmation": result.get("requires_confirmation", False),
            "pending_action": result.get("pending_action"),
            "tool_output": result.get("tool_output", {}),
            "session": result.get("session", {}),
        }
        # Bubble up session changes so the supervisor can persist them
        state["session"] = result.get("session", state.get("session", {}))
        return state

    def _build_graph(self) -> Any:
        graph = StateGraph(AgentState)
        graph.add_node("intent_understanding", self._intent_node)
        graph.add_node("create_branch", self._create_branch)
        graph.add_node("read_branch", self._read_branch)
        graph.add_node("update_branch", self._update_branch)
        graph.add_node("delete_branch", self._delete_branch)
        graph.add_node("mcp_tool_execution", self._execute_tool)
        graph.add_node("result_response", self._response_node)

        graph.set_entry_point("intent_understanding")
        graph.add_conditional_edges(
            "intent_understanding",
            self._route_intent,
            {
                "create": "create_branch",
                "read": "read_branch",
                "update": "update_branch",
                "delete": "delete_branch",
                "response": "result_response",
            },
        )
        for node in ("create_branch", "read_branch", "update_branch", "delete_branch"):
            graph.add_conditional_edges(
                node,
                lambda s: "execute" if s.get("tool_name") else "response",
                {"execute": "mcp_tool_execution", "response": "result_response"},
            )
        graph.add_edge("mcp_tool_execution", "result_response")
        graph.add_edge("result_response", END)
        return graph.compile()

    # ── nodes ─────────────────────────────────────────────────────────────────

    async def _intent_node(self, state: AgentState) -> AgentState:
        query = state["user_query"].strip()
        lower = query.lower()
        session = state.get("session", {})

        # ── Pending confirmation (yes/no) ─────────────────────────────────
        if session.get("pending_action") == "crud" and _is_yes(lower):
            state["intent"] = session.get("crud_intent", "create")
            session["confirmation"] = True
            state["session"] = session
            return state

        if session.get("pending_action") and _is_no(lower):
            session.clear()
            state["session"] = session
            state["intent"] = "cancel"
            state["response"] = "Canceled. No changes were made."
            return state

        # ── Detect explicit non-create intent BEFORE checking draft ───────
        # If the user clearly wants to READ, DELETE, or UPDATE, we must
        # honour that even if an incomplete draft is sitting in the session.
        # Without this check, "show all surveys" while a draft exists would
        # silently continue collecting draft fields instead of listing surveys.
        is_read   = bool(re.search(r"\b(show|list|find|search|get|display|fetch|view|all surveys?)\b", lower))
        is_delete = bool(re.search(r"\b(delete|remove)\b", lower))
        is_update = bool(re.search(r"\b(update|change|modify)\b", lower))

        if (is_read or is_delete or is_update) and session.get("draft"):
            # Abandon the stale draft — user has moved on
            session.pop("draft", None)
            session.pop("pending_action", None)
            session.pop("crud_intent", None)
            state["session"] = session

        # ── Active create draft — continue collecting fields ───────────────
        if session.get("draft") and not is_read and not is_delete and not is_update:
            state["intent"] = "create"
            return state

        # ── Fresh intent detection ─────────────────────────────────────────
        if re.search(r"\b(create|add|new survey)\b", lower):
            state["intent"] = "create"
        elif is_delete:
            state["intent"] = "delete"
        elif is_update:
            state["intent"] = "update"
        elif is_read or re.search(r"\b(how many|count)\b", lower):
            state["intent"] = "read"
        else:
            state["intent"] = "read"  # safe default
        return state

    def _route_intent(self, state: AgentState) -> str:
        intent = state.get("intent", "")
        if intent in {"create", "read", "update", "delete"}:
            return intent
        return "response"

    async def _create_branch(self, state: AgentState) -> AgentState:
        session = state.get("session", {})
        draft = SurveyDraft.model_validate(session.get("draft", {}))
        draft = _merge_draft(draft, _extract_survey_fields(state["user_query"]))
        session["draft"] = draft.as_payload()

        missing = _missing_fields(draft)
        if missing:
            state["response"] = _missing_prompt(draft, missing)
            state["session"] = session
            return state

        if not session.get("confirmation"):
            session["pending_action"] = "crud"   # supervisor routes to crud agent
            session["crud_intent"] = "create"      # crud agent internal op
            state["response"] = (
                "Please confirm this survey before I create it:\n\n"
                + _format_survey(draft.as_payload())
                + "\n\nReply yes to create it, or no to cancel."
            )
            state["requires_confirmation"] = True
            state["pending_action"] = "crud"
            state["session"] = session
            return state

        state["tool_name"] = "create_survey"
        state["tool_args"] = {"payload": draft.as_payload()}
        return state

    async def _read_branch(self, state: AgentState) -> AgentState:
        filters = _extract_filters(state["user_query"])
        survey_id = filters.pop("survey_id", None)
        if survey_id:
            state["tool_name"] = "get_survey_by_id"
            state["tool_args"] = {"survey_id": survey_id}
        else:
            state["tool_name"] = "search_surveys" if filters else "list_surveys"
            state["tool_args"] = filters
        return state

    async def _update_branch(self, state: AgentState) -> AgentState:
        session = state.get("session", {})
        query_lower = state["user_query"].lower()
        
        # Check if this is a NEW update request (not a continuation of confirmation)
        is_new_update_request = bool(re.search(r"\b(update|change|modify)\b", query_lower))
        
        if session.get("confirmation") and not is_new_update_request:
            # This is a confirmation ("yes") for a previous update request
            state["tool_name"] = "update_survey"
            state["tool_args"] = {
                "survey_id": session["selected_survey"]["id"],
                "changes": session["changes"],
            }
            return state
        
        # New update request - clear any stale confirmation state
        if is_new_update_request:
            session.pop("confirmation", None)
            session.pop("selected_survey", None)
            session.pop("changes", None)

        self._multiple_matches = []  # Reset before resolving
        target = await self._resolve_target(state["user_query"])
        changes = _extract_update_changes(state["user_query"])
        
        if not target:
            if self._multiple_matches:
                # Multiple surveys found - show list and ask for ID
                rows = [_format_survey_line(s) for s in self._multiple_matches[:5]]
                state["response"] = (
                    f"Found {len(self._multiple_matches)} matching survey(s). "
                    f"Please specify which one by ID:\n" + "\n".join(rows)
                )
            else:
                state["response"] = "I could not find a matching survey. Try using the survey ID or full name."
            return state
            
        if not changes:
            state["response"] = "What would you like to change? E.g.: change recommendation to Likely."
            return state

        session["pending_action"] = "crud"   # supervisor routes to crud agent
        session["crud_intent"] = "update"      # crud agent internal op
        session["selected_survey"] = target
        session["changes"] = changes
        state["response"] = (
            "I found this survey and prepared the update:\n\n"
            + _format_survey(target)
            + "\n\nChanges:\n"
            + json.dumps(changes, indent=2)
            + "\n\nReply yes to apply, or no to cancel."
        )
        state["requires_confirmation"] = True
        state["pending_action"] = "crud"
        state["session"] = session
        return state

    async def _delete_branch(self, state: AgentState) -> AgentState:
        session = state.get("session", {})
        query_lower = state["user_query"].lower()
        
        # Check if this is a NEW delete request (not a continuation of confirmation)
        is_new_delete_request = bool(re.search(r"\b(delete|remove)\b", query_lower))
        
        if session.get("confirmation") and not is_new_delete_request:
            # This is a confirmation ("yes") for a previous delete request
            state["tool_name"] = "delete_survey"
            state["tool_args"] = {"survey_id": session["selected_survey"]["id"]}
            return state
        
        # New delete request - clear any stale confirmation state
        if is_new_delete_request:
            session.pop("confirmation", None)
            session.pop("selected_survey", None)

        self._multiple_matches = []  # Reset before resolving
        target = await self._resolve_target(state["user_query"])
        
        if not target:
            if self._multiple_matches:
                # Multiple surveys found - show list and ask for ID
                rows = [_format_survey_line(s) for s in self._multiple_matches[:5]]
                state["response"] = (
                    f"Found {len(self._multiple_matches)} matching survey(s). "
                    f"Please specify which one by ID:\n" + "\n".join(rows)
                )
            else:
                state["response"] = "I could not find a matching survey to delete."
            return state

        session["pending_action"] = "crud"   # supervisor routes to crud agent
        session["crud_intent"] = "delete"      # crud agent internal op
        session["selected_survey"] = target
        state["response"] = (
            "I found this survey:\n\n"
            + _format_survey(target)
            + "\n\nDo you want to delete it? Reply yes or no."
        )
        state["requires_confirmation"] = True
        state["pending_action"] = "crud"
        state["session"] = session
        return state

    async def _execute_tool(self, state: AgentState) -> AgentState:
        tool_output = await self.tools.call(
            state["tool_name"] or "", state.get("tool_args", {})
        )
        state["tool_output"] = tool_output
        
        # For updates, fetch the survey again to ensure we show the latest data
        if state.get("intent") == "update" and tool_output.get("ok"):
            survey_id = state.get("tool_args", {}).get("survey_id")
            if survey_id:
                fresh = await self.tools.call("get_survey_by_id", {"survey_id": survey_id})
                if fresh.get("ok"):
                    state["tool_output"] = fresh
        
        if state.get("intent") in {"create", "update", "delete"}:
            state["session"] = {}
        return state

    async def _response_node(self, state: AgentState) -> AgentState:
        if state.get("response"):
            return state
        output = state.get("tool_output", {})
        intent = state.get("intent", "")
        if not output.get("ok", True):
            state["response"] = output.get("message", "The tool call failed.")
        elif intent == "create":
            state["response"] = "✅ Created the survey:\n\n" + _format_survey(output["survey"])
        elif intent == "update":
            # Show what was changed
            changes = state.get("tool_args", {}).get("changes", {})
            changes_text = "\n".join(f"  • {k}: {v}" for k, v in changes.items())
            state["response"] = (
                f"✅ Updated the survey successfully!\n\n"
                f"Changes applied:\n{changes_text}\n\n"
                f"Updated survey details:\n{_format_survey(output['survey'])}"
            )
            # Clear session after successful update
            state["session"] = {}
        elif intent == "delete":
            state["response"] = "✅ " + output.get("message", "Deleted successfully.")
            # Clear session after successful delete
            state["session"] = {}
        elif output.get("survey"):
            state["response"] = "I found this survey:\n\n" + _format_survey(output["survey"])
        else:
            surveys = output.get("surveys", [])
            if not surveys:
                state["response"] = "No matching surveys found."
            elif len(surveys) == 1:
                # Single result — show full details
                state["response"] = "I found this survey:\n\n" + _format_survey(surveys[0])
            else:
                # Multiple results — show summary list
                rows = [_format_survey_line(s) for s in surveys[:10]]
                state["response"] = f"Found {len(surveys)} survey(s):\n" + "\n".join(rows)
        return state

    async def _resolve_target(self, query: str) -> dict[str, Any] | None:
        """
        Resolve a single target survey for update/delete operations.
        Returns the survey dict if exactly 1 match, otherwise None.
        """
        sid = _extract_id(query)
        if sid:
            out = await self.tools.call("get_survey_by_id", {"survey_id": sid})
            return out.get("survey") if out.get("ok") else None
        # Use for_search=False to only match by name/ID, not field values
        filters = _extract_filters(query, for_search=False)
        out = await self.tools.call("search_surveys", filters)
        surveys = out.get("surveys", [])
        
        if len(surveys) == 1:
            return surveys[0]
        elif len(surveys) > 1:
            # Store info for better error message
            self._multiple_matches = surveys
            return None
        else:
            return None


# ── Pure helper functions (unchanged from your original graph.py) ─────────────

def _extract_survey_fields(text: str) -> dict[str, Any]:
    lower = text.lower()
    fields: dict[str, Any] = {}
    name = _extract_name(text)
    if name:
        first, last = name
        if first:
            fields["first_name"] = first
        if last:   # only set last_name if actually found — empty string = first-name-only search
            fields["last_name"] = last
    fields.update(_extract_labeled_values(text))
    labeled = {
        "zip_code": r"(?:zip_code|zip code|zip)\s*(?:is|:)?\s*(\d{5}(?:-\d{4})?)",
        "telephone": r"(?:telephone|phone|phone number)\s*(?:is|:)?\s*((?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        "email": r"email\s*(?:is|:)?\s*([\w.+-]+@[\w-]+\.[\w.-]+)",
        "date_of_survey": r"(?:date_of_survey|survey date|date)\s*(?:is|:)?\s*([A-Za-z]+|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
        "recommendation": r"(?:recommendation|recommendation likelihood)\s*(?:is|:)?\s*([A-Za-z ]+)",
    }
    for field, pattern in labeled.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().rstrip(",")
            if field == "date_of_survey":
                parsed = _parse_date_value(val)
                if parsed:
                    fields[field] = parsed
            elif field == "recommendation":
                parsed = _parse_recommendation(val)
                if parsed:
                    fields[field] = parsed
            else:
                fields[field] = val
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    if email:
        fields["email"] = email.group(0)
    phone = re.search(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", text)
    if phone:
        fields["telephone"] = phone.group(0)
    parsed_date = _parse_date_value(text)
    if parsed_date:
        fields["date_of_survey"] = parsed_date
    zip_code = re.search(r"\b\d{5}(?:-\d{4})?\b", text)
    if zip_code:
        fields["zip_code"] = zip_code.group(0)
    address = re.search(
        r"(?:address is|at)\s+(.+?),\s*([A-Za-z .'-]+)\s+([A-Z]{2})\s+\d{5}",
        text, re.IGNORECASE,
    )
    if address:
        fields["street_address"] = address.group(1).strip()
        fields["city"] = address.group(2).strip()
        fields["state"] = address.group(3).strip()
    for option in INTEREST_OPTIONS:
        if option in lower:
            fields["interest_source"] = option
            break
    parsed_rec = _parse_recommendation(lower)
    if parsed_rec:
        fields["recommendation"] = parsed_rec
    liked = sorted({v for alias, v in LIKED_ALIASES.items() if alias in lower})
    if liked:
        fields["liked_most"] = liked
    return fields


def _extract_labeled_values(text: str) -> dict[str, Any]:
    label_map = {
        "first name": "first_name", "first_name": "first_name", "firstname": "first_name",
        "last name": "last_name", "last_name": "last_name", "lastname": "last_name",
        "street address": "street_address", "street_address": "street_address",
        "address": "street_address", "city": "city", "state": "state",
        "zip code": "zip_code", "zip_code": "zip_code", "zip": "zip_code",
        "telephone": "telephone", "phone": "telephone", "phone number": "telephone",
        "email": "email", "date_of_survey": "date_of_survey",
        "survey date": "date_of_survey", "date": "date_of_survey",
        "recommendation": "recommendation", "recommendation likelihood": "recommendation",
        "interest source": "interest_src", "interest_source": "interest_src",
        "liked most": "liked_most", "liked_most": "liked_most",
        "what they liked most": "liked_most", "they liked most": "liked_most",
    }
    labels = sorted(label_map, key=len, reverse=True)
    label_pat = "|".join(re.escape(l) for l in labels)
    pattern = re.compile(
        rf"(?P<label>{label_pat})\s*(?:is|:)?\s*"
        rf"(?P<value>.*?)(?=,\s*(?:{label_pat})\s*(?:is|:)?|\s+(?:{label_pat})\s*(?:is|:)|$)",
        re.IGNORECASE,
    )
    fields: dict[str, Any] = {}
    for m in pattern.finditer(text):
        field = label_map[m.group("label").lower()]
        value = m.group("value").strip().strip(",.;")
        if not value:
            continue
        if field == "date_of_survey":
            p = _parse_date_value(value)
            if p:
                fields[field] = p
        elif field == "recommendation":
            p = _parse_recommendation(value)
            if p:
                fields[field] = p
        else:
            fields[field] = value
    return fields


def _merge_draft(draft: SurveyDraft, fields: dict[str, Any]) -> SurveyDraft:
    data = draft.as_payload()
    for key, value in fields.items():
        if key == "liked_most":
            data[key] = sorted(set(data.get(key, []) + value))
        else:
            data[key] = value
    return SurveyDraft.model_validate(data)


def _missing_fields(draft: SurveyDraft) -> list[str]:
    payload = draft.as_payload()
    return [f for f in REQUIRED_FIELDS if not payload.get(f)]


def _missing_prompt(draft: SurveyDraft, missing: list[str]) -> str:
    known = draft.as_payload()
    prompt = "I started the survey draft."
    if known:
        prompt += "\n\nKnown so far:\n" + _format_survey(known)
    readable = [FIELD_LABELS.get(f, f) for f in missing]
    prompt += "\n\nPlease provide: " + ", ".join(readable) + "."
    return prompt


def _parse_date_value(text: str) -> str | None:
    if re.search(r"\btoday\b", text.lower()):
        return date.today().isoformat()
    iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso:
        return iso.group(0)
    slash = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if slash:
        try:
            return datetime.strptime(slash.group(0), "%m/%d/%Y").date().isoformat()
        except ValueError:
            return None
    return None


def _parse_recommendation(text: str) -> str | None:
    lower = text.lower().strip()
    for phrase, value in sorted(
        RECOMMENDATION_ALIASES.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if re.search(rf"\b{re.escape(phrase)}\b", lower):
            return value
    return None


def _extract_filters(text: str, for_search: bool = True) -> dict[str, Any]:
    """
    Build a filter dict from a query.
    
    Args:
        text: The user query
        for_search: If True, include field values for filtering (read operations).
                   If False, only match by name/ID (update/delete operations).
    """
    fields = _extract_survey_fields(text)
    filters: dict[str, Any] = {}

    # Name filters — always include
    if fields.get("first_name"):
        filters["first_name"] = fields["first_name"]
    if fields.get("last_name"):
        filters["last_name"] = fields["last_name"]

    # Field filters — only for search operations, NOT for update/delete
    # (We don't want to filter by the NEW value we're trying to set)
    if for_search:
        for k in ("interest_source", "recommendation"):
            if fields.get(k):
                filters[k] = fields[k]

        if fields.get("liked_most"):
            filters["liked_most"] = fields["liked_most"][0]

    sid = _extract_id(text)
    if sid:
        filters["survey_id"] = sid

    return filters


def _extract_update_changes(text: str) -> dict[str, Any]:
    fields = _extract_survey_fields(text)
    return {k: v for k, v in fields.items() if k not in {"first_name", "last_name"}}


def _extract_name(text: str) -> tuple[str, str] | None:
    """
    Extract first + last name from a query.
    Handles: Title Case, lowercase, single/multi-word names, various prepositions.
    Returns (first_name, last_name) where last_name may be empty string.
    """
    STOP_WORDS = {
        "all", "surveys", "survey", "me", "the", "a", "an", "my",
        "where", "liked", "from", "with", "recommendation", "show", "find",
        "get", "for", "by", "first", "last", "latest", "oldest", "new", "old",
        "any", "some", "name", "names", "of", "delete", "update", "change",
        "as", "to", "is", "are", "email", "phone", "telephone", "address",
        "city", "state", "zip", "date", "interest", "source", "comments",
        "record", "records",  # Don't include these in names
        "create", "add",  # Don't parse "create a survey" as name "create"
        "another", "with",  # Don't parse "add another" as name
    }
    
    # Pattern 0: Explicit "first name: X, last name: Y" format (highest priority)
    # "add survey with first name: Sudhir, last name: Chaudhary"
    # "create survey first_name: Jane, last_name: Smith"
    m = re.search(
        r"first[_\s]?name\s*[:\s]\s*([a-zA-Z]+)[,\s]+last[_\s]?name\s*[:\s]\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)*)",
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip().title(), m.group(2).strip().title()
    
    # Pattern 1: Trigger word + name(s) — handles both single and multi-word names
    # Stops at field keywords like "recommendation", "email", "to", "as"
    # Allows punctuation (periods, commas) before stop words
    # "update vivek recommendation" → captures "vivek"
    # "find john doe" → captures "john doe"
    # "Create a survey for Jane Smith. She liked" → captures "Jane Smith"
    m = re.search(
        r"(?:for|find|delete|remove|update|change|by|show|get)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*?)(?:[.,;!?\s]+(?:recommendation|email|phone|telephone|address|city|state|zip|date|interest|liked|to|as|is|are|survey|surveys|she|he|their|'s|\band\b|\bor\b)|[.,;!?\s]*$)",
        text, re.IGNORECASE
    )
    if m:
        name_text = m.group(1).strip()
        parts = [p for p in name_text.split() if p.lower() not in STOP_WORDS]
        if parts:
            if len(parts) >= 2:
                return parts[0].title(), " ".join(p.title() for p in parts[1:])
            elif len(parts) == 1:
                return parts[0].title(), ""

    # Pattern 2: Name at start + trigger word
    # "vivek find", "john search", "Jane Doe show"
    m = re.search(
        r"^([a-zA-Z]+(?:\s+[a-zA-Z]+)*?)\s+(?:find|search|show|get|delete|update)",
        text, re.IGNORECASE
    )
    if m:
        name_text = m.group(1).strip()
        parts = [p for p in name_text.split() if p.lower() not in STOP_WORDS]
        if parts:
            if len(parts) >= 2:
                return parts[0].title(), " ".join(p.title() for p in parts[1:])
            elif len(parts) == 1:
                return parts[0].title(), ""

    # Pattern 3: Name + "survey" or "'s" (no trigger word needed)
    # "Vivek survey", "vivek survey", "John Doe survey", "jane's"
    m = re.search(
        r"\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*?)\s*(?:survey|surveys|'s)",
        text, re.IGNORECASE
    )
    if m:
        name_text = m.group(1).strip()
        parts = [p for p in name_text.split() if p.lower() not in STOP_WORDS]
        if parts:
            if len(parts) >= 2:
                return parts[0].title(), " ".join(p.title() for p in parts[1:])
            elif len(parts) == 1:
                return parts[0].title(), ""

    # Pattern 4: "name is/:" followed by name
    # "find survey name vivek", "survey name is John Doe"
    m = re.search(
        r"(?:name|names)\s+(?:is|are|:)?\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)*)",
        text, re.IGNORECASE
    )
    if m:
        name_text = m.group(1).strip()
        parts = [p for p in name_text.split() if p.lower() not in STOP_WORDS]
        if parts:
            if len(parts) >= 2:
                return parts[0].title(), " ".join(p.title() for p in parts[1:])
            elif len(parts) == 1:
                return parts[0].title(), ""

    return None


def _extract_id(text: str) -> int | None:
    """
    Extract a numeric survey ID from text.
    Handles: 'survey 3', 'id 5', '#3', 'number 3', 'no. 3',
             '1st survey', '2nd', '3rd', 'first survey' (→ 1).
    """
    lower = text.lower()

    # Explicit numeric ID patterns
    m = re.search(
        r"(?:survey\s*#?|id\s*#?|number\s*#?|no\.?\s*#?|survey\s+no\.?\s*)(\d+)",
        lower
    )
    if m:
        return int(m.group(1))

    # Standalone digit: "survey 3", "get survey 5"
    m = re.search(r"\bsurvey\s+(\d+)\b", lower)
    if m:
        return int(m.group(1))

    # Ordinal words: "first" → 1, "second" → 2, etc.
    ORDINALS = {
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
        "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5,
    }
    for word, num in ORDINALS.items():
        if re.search(rf"\b{word}\b", lower):
            return num

    return None


def _is_yes(text: str) -> bool:
    return text.strip() in {"yes", "y", "confirm", "approve", "approved", "do it"}


def _is_no(text: str) -> bool:
    return text.strip() in {"no", "n", "cancel", "stop", "do not"}


def _format_survey(survey: dict[str, Any]) -> str:
    labels = {
        "id": "ID", "first_name": "First name", "last_name": "Last name",
        "street_address": "Street address", "city": "City", "state": "State",
        "zip_code": "Zip", "telephone": "Telephone", "email": "Email",
        "date_of_survey": "Survey date", "liked_most": "Liked most",
        "interest_source": "Interest source", "recommendation": "Recommendation",
        "raffle": "Raffle", "comments": "Comments",
    }
    lines = []
    for key, label in labels.items():
        if survey.get(key):
            val = survey[key]
            if isinstance(val, list):
                val = ", ".join(val)
            lines.append(f"- {label}: {val}")
    return "\n".join(lines)


def _format_survey_line(survey: dict[str, Any]) -> str:
    liked = ", ".join(survey.get("liked_most", []))
    return (
        f"- #{survey.get('id')} {survey.get('first_name')} {survey.get('last_name')} "
        f"({survey.get('date_of_survey')}): liked {liked}; "
        f"recommendation {survey.get('recommendation')}"
    )