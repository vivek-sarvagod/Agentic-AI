import json
import re
from datetime import date, datetime
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings
from models import SurveyDraft
from tool_client import SurveyToolClient

Intent = Literal["create", "read", "update", "delete", "confirm", "cancel", "unknown"]

REQUIRED_FIELDS = [
    "first_name",
    "last_name",
    "street_address",
    "city",
    "state",
    "zip_code",
    "telephone",
    "email",
    "date_of_survey",
    "liked_most",
    "interest_source",
    "recommendation",
]

LIKED_ALIASES = {
    "students": "students",
    "location": "location",
    "campus": "campus",
    "atmosphere": "atmosphere",
    "dorm": "dorm_rooms",
    "dorms": "dorm_rooms",
    "dorm rooms": "dorm_rooms",
    "sports": "sports",
}

INTEREST_OPTIONS = {"friends", "television", "internet", "other"}
RECOMMENDATION_ALIASES = {
    "very likely": "Very Likely",
    "likely": "Likely",
    "unlikely": "Unlikely",
    "yes": "Likely",
    "recommend": "Likely",
    "would recommend": "Likely",
    "no": "Unlikely",
    "not recommend": "Unlikely",
}

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


class AgentState(TypedDict, total=False):
    session: dict[str, Any]
    user_query: str
    intent: Intent
    tool_name: str | None
    tool_args: dict[str, Any]
    tool_output: dict[str, Any]
    response: str
    requires_confirmation: bool
    pending_action: str | None
    selected_survey: dict[str, Any] | None
    draft: dict[str, Any]
    changes: dict[str, Any]


class SurveyAgent:
    def __init__(self) -> None:
        self.tools = SurveyToolClient()
        self.graph = self._build_graph()

    async def run(self, message: str, session: dict[str, Any]) -> dict[str, Any]:
        state: AgentState = {"user_query": message, "session": session}
        result = await self.graph.ainvoke(state)
        session.update(result.get("session", {}))
        return result

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("input", self._input_node)
        graph.add_node("intent_understanding", self._intent_node)
        graph.add_node("create_branch", self._create_branch)
        graph.add_node("read_branch", self._read_branch)
        graph.add_node("update_branch", self._update_branch)
        graph.add_node("delete_branch", self._delete_branch)
        graph.add_node("mcp_tool_execution", self._execute_tool)
        graph.add_node("result_response", self._response_node)

        graph.set_entry_point("input")
        graph.add_edge("input", "intent_understanding")
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
                self._route_after_branch,
                {"execute": "mcp_tool_execution", "response": "result_response"},
            )
        graph.add_edge("mcp_tool_execution", "result_response")
        graph.add_edge("result_response", END)
        return graph.compile()

    async def _input_node(self, state: AgentState) -> AgentState:
        return state

    async def _intent_node(self, state: AgentState) -> AgentState:
        query = state["user_query"].strip()
        lower = query.lower()
        session = state.get("session", {})

        if session.get("pending_action") and _is_yes(lower):
            state["intent"] = session["pending_action"]
            state["requires_confirmation"] = False
            session["confirmation"] = True
            return state
        if session.get("pending_action") and _is_no(lower):
            state["intent"] = "cancel"
            session.clear()
            state["response"] = "Canceled. No survey changes were made."
            return state

        if session.get("draft"):
            state["intent"] = "create"
            return state

        llm_intent = await self._classify_with_llm(query)
        if llm_intent:
            state["intent"] = llm_intent
        elif re.search(r"\b(create|add|new survey)\b", lower):
            state["intent"] = "create"
        elif re.search(r"\b(delete|remove)\b", lower):
            state["intent"] = "delete"
        elif re.search(r"\b(update|change|modify)\b", lower):
            state["intent"] = "update"
        elif re.search(r"\b(show|list|find|search|how many|count)\b", lower):
            state["intent"] = "read"
        else:
            state["intent"] = "unknown"
            state["response"] = self._help_text()
        return state

    async def _classify_with_llm(self, query: str) -> Intent | None:
        if not settings.OPENAI_API_KEY:
            return None
        try:            

            model = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0,
            )
            response = await model.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "Classify the user request for a student survey CRUD agent. "
                            "Return only one word: create, read, update, delete, or unknown."
                        )
                    ),
                    HumanMessage(content=query),
                ]
            )
            intent = str(response.content).strip().lower()
            if intent in {"create", "read", "update", "delete", "unknown"}:
                return intent  # type: ignore[return-value]
        except Exception:
            return None
        return None

    def _route_intent(self, state: AgentState) -> str:
        intent = state.get("intent")
        if intent in {"create", "read", "update", "delete"}:
            return intent
        return "response"

    def _route_after_branch(self, state: AgentState) -> str:
        return "execute" if state.get("tool_name") else "response"

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
            session["pending_action"] = "create"
            state["response"] = "Please confirm this survey before I create it:\n\n" + _format_survey(
                draft.as_payload()
            ) + "\n\nReply yes to create it, or no to cancel."
            state["requires_confirmation"] = True
            state["pending_action"] = "create"
            state["session"] = session
            return state

        state["tool_name"] = "create_survey"
        state["tool_args"] = {"payload": draft.as_payload()}
        return state

    async def _read_branch(self, state: AgentState) -> AgentState:
        query = state["user_query"]
        filters = _extract_filters(query)
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
        query = state["user_query"]

        if session.get("confirmation"):
            state["tool_name"] = "update_survey"
            state["tool_args"] = {
                "survey_id": session["selected_survey"]["id"],
                "changes": session["changes"],
            }
            return state

        target = await self._resolve_target(query)
        changes = _extract_update_changes(query)
        if not target:
            state["response"] = "I could not find a matching survey to update. Try using the survey ID or full name."
            return state
        if not changes:
            state["response"] = "What would you like me to change? For example: change recommendation to Likely."
            return state

        session["pending_action"] = "update"
        session["selected_survey"] = target
        session["changes"] = changes
        state["response"] = (
            "I found this survey and prepared the update:\n\n"
            + _format_survey(target)
            + "\n\nChanges:\n"
            + json.dumps(changes, indent=2)
            + "\n\nReply yes to apply the update, or no to cancel."
        )
        state["requires_confirmation"] = True
        state["pending_action"] = "update"
        state["session"] = session
        return state

    async def _delete_branch(self, state: AgentState) -> AgentState:
        session = state.get("session", {})
        if session.get("confirmation"):
            state["tool_name"] = "delete_survey"
            state["tool_args"] = {"survey_id": session["selected_survey"]["id"]}
            return state

        target = await self._resolve_target(state["user_query"])
        if not target:
            state["response"] = "I could not find a matching survey to delete. Try using the survey ID or full name."
            return state

        session["pending_action"] = "delete"
        session["selected_survey"] = target
        state["response"] = (
            "I found this survey:\n\n"
            + _format_survey(target)
            + "\n\nDo you want me to delete it? Reply yes to delete, or no to cancel."
        )
        state["requires_confirmation"] = True
        state["pending_action"] = "delete"
        state["session"] = session
        return state

    async def _execute_tool(self, state: AgentState) -> AgentState:
        state["tool_output"] = await self.tools.call(state["tool_name"] or "", state.get("tool_args", {}))
        if state.get("intent") in {"create", "update", "delete"}:
            state["session"] = {}
        return state

    async def _response_node(self, state: AgentState) -> AgentState:
        if state.get("response"):
            return state

        output = state.get("tool_output", {})
        intent = state.get("intent", "unknown")
        if not output.get("ok", True):
            state["response"] = output.get("message", "The tool call failed.")
        elif intent == "create":
            state["response"] = "Created the survey successfully:\n\n" + _format_survey(output["survey"])
        elif intent == "update":
            state["response"] = "Updated the survey successfully:\n\n" + _format_survey(output["survey"])
        elif intent == "delete":
            state["response"] = output.get("message", "Deleted the survey successfully.")
        elif output.get("survey"):
            state["response"] = "I found this survey:\n\n" + _format_survey(output["survey"])
        else:
            surveys = output.get("surveys", [])
            if "how many" in state["user_query"].lower() or "count" in state["user_query"].lower():
                state["response"] = f"I found {len(surveys)} matching survey(s)."
            elif not surveys:
                state["response"] = "I did not find any matching surveys."
            else:
                rows = [_format_survey_line(survey) for survey in surveys[:10]]
                state["response"] = f"I found {len(surveys)} survey(s):\n" + "\n".join(rows)
        return state

    async def _resolve_target(self, query: str) -> dict[str, Any] | None:
        survey_id = _extract_id(query)
        if survey_id:
            output = await self.tools.call("get_survey_by_id", {"survey_id": survey_id})
            return output.get("survey") if output.get("ok") else None

        filters = _extract_filters(query)
        output = await self.tools.call("search_surveys", filters)
        surveys = output.get("surveys", [])
        return surveys[0] if len(surveys) == 1 else None

    @staticmethod
    def _help_text() -> str:
        return (
            "I can create, find, update, and delete student surveys. "
            "Try: 'Create a survey for Jane Smith', 'Show surveys where students liked dorm rooms', "
            "'Change John Doe's recommendation to Likely', or 'Delete survey 12'."
        )


def _extract_survey_fields(text: str) -> dict[str, Any]:
    lower = text.lower()
    fields: dict[str, Any] = {}
    name = _extract_name(text)
    if name:
        fields["first_name"], fields["last_name"] = name
    fields.update(_extract_labeled_values(text))
    labeled_fields = {
        "zip_code": r"(?:zip_code|zip code|zip)\s*(?:is|:)?\s*(\d{5}(?:-\d{4})?)",
        "telephone": r"(?:telephone|phone|phone number)\s*(?:is|:)?\s*((?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        "email": r"email\s*(?:is|:)?\s*([\w.+-]+@[\w-]+\.[\w.-]+)",
        "date_of_survey": r"(?:date_of_survey|survey date|date)\s*(?:is|:)?\s*([A-Za-z]+|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})",
        "recommendation": r"(?:recommendation|recommendation likelihood)\s*(?:is|:)?\s*([A-Za-z ]+)",
    }
    for field, pattern in labeled_fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip().rstrip(",")
            if field == "date_of_survey":
                parsed_date = _parse_date_value(value)
                if parsed_date:
                    fields[field] = parsed_date
            elif field == "recommendation":
                parsed_recommendation = _parse_recommendation(value)
                if parsed_recommendation:
                    fields[field] = parsed_recommendation
            else:
                fields[field] = value
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
        text,
        re.IGNORECASE,
    )
    if address:
        fields["street_address"] = address.group(1).strip()
        fields["city"] = address.group(2).strip()
        fields["state"] = address.group(3).strip()
    else:
        city_state = re.search(
            r"\b([A-Za-z .'-]+),?\s+([A-Z]{2})\s+\d{5}\b",
            text,
        )
        if city_state and "city" in lower:
            fields["city"] = city_state.group(1).strip()
            fields["state"] = city_state.group(2).strip()
    for option in INTEREST_OPTIONS:
        if option in lower:
            fields["interest_source"] = option
            break
    parsed_recommendation = _parse_recommendation(lower)
    if parsed_recommendation:
        fields["recommendation"] = parsed_recommendation
    liked = sorted({value for alias, value in LIKED_ALIASES.items() if alias in lower})
    if liked:
        fields["liked_most"] = liked
    return fields


def _extract_labeled_values(text: str) -> dict[str, Any]:
    label_map = {
        "street address": "street_address",
        "street_address": "street_address",
        "address": "street_address",
        "city": "city",
        "state": "state",
        "zip code": "zip_code",
        "zip_code": "zip_code",
        "zip": "zip_code",
        "telephone": "telephone",
        "phone": "telephone",
        "phone number": "telephone",
        "email": "email",
        "date_of_survey": "date_of_survey",
        "survey date": "date_of_survey",
        "date": "date_of_survey",
        "recommendation": "recommendation",
        "recommendation likelihood": "recommendation",
    }
    labels = sorted(label_map, key=len, reverse=True)
    label_pattern = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf"(?P<label>{label_pattern})\s*(?:is|:)?\s*"
        rf"(?P<value>.*?)(?=,\s*(?:{label_pattern})\s*(?:is|:)?|\s+(?:{label_pattern})\s*(?:is|:)|$)",
        re.IGNORECASE,
    )

    fields: dict[str, Any] = {}
    for match in pattern.finditer(text):
        field = label_map[match.group("label").lower()]
        value = match.group("value").strip().strip(",.;")
        if not value:
            continue
        if field == "date_of_survey":
            parsed_date = _parse_date_value(value)
            if parsed_date:
                fields[field] = parsed_date
        elif field == "recommendation":
            parsed_recommendation = _parse_recommendation(value)
            if parsed_recommendation:
                fields[field] = parsed_recommendation
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
    missing = []
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or value == "" or value == []:
            missing.append(field)
    return missing


def _missing_prompt(draft: SurveyDraft, missing: list[str]) -> str:
    known = draft.as_payload()
    prompt = "I started the survey draft."
    if known:
        prompt += "\n\nKnown so far:\n" + _format_survey(known)
    readable_missing = [FIELD_LABELS.get(field, field) for field in missing]
    prompt += "\n\nPlease provide the missing field(s): " + ", ".join(readable_missing) + "."
    return prompt


def _parse_date_value(text: str) -> str | None:
    lower = text.lower()
    if re.search(r"\btoday\b", lower):
        return date.today().isoformat()

    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if iso_match:
        return iso_match.group(0)

    slash_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text)
    if slash_match:
        try:
            return datetime.strptime(slash_match.group(0), "%m/%d/%Y").date().isoformat()
        except ValueError:
            return None

    return None


def _parse_recommendation(text: str) -> str | None:
    lower = text.lower().strip()
    for phrase, value in sorted(RECOMMENDATION_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(phrase)}\b", lower):
            return value
    return None


def _extract_filters(text: str) -> dict[str, Any]:
    fields = _extract_survey_fields(text)
    filters = {
        key: fields[key]
        for key in ("first_name", "last_name", "interest_source", "recommendation")
        if key in fields
    }
    if fields.get("liked_most"):
        filters["liked_most"] = fields["liked_most"][0]
    survey_id = _extract_id(text)
    if survey_id:
        filters["survey_id"] = survey_id
    return filters


def _extract_update_changes(text: str) -> dict[str, Any]:
    fields = _extract_survey_fields(text)
    return {
        key: value
        for key, value in fields.items()
        if key not in {"first_name", "last_name"}
    }


def _extract_name(text: str) -> tuple[str, str] | None:
    patterns = [
        r"(?:for|find|delete|remove|update|change)\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)",
        r"([A-Z][a-z]+)\s+([A-Z][a-z]+)'s",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1), match.group(2)
    return None


def _extract_id(text: str) -> int | None:
    match = re.search(r"(?:survey\s*#?|id\s*#?)\s*(\d+)", text.lower())
    return int(match.group(1)) if match else None


def _is_yes(text: str) -> bool:
    return text.strip() in {"yes", "y", "confirm", "approved", "approve", "do it"}


def _is_no(text: str) -> bool:
    return text.strip() in {"no", "n", "cancel", "stop", "do not"}


def _format_survey(survey: dict[str, Any]) -> str:
    lines = []
    labels = {
        "id": "ID",
        "first_name": "First name",
        "last_name": "Last name",
        "street_address": "Street address",
        "city": "City",
        "state": "State",
        "zip_code": "Zip",
        "telephone": "Telephone",
        "email": "Email",
        "date_of_survey": "Survey date",
        "liked_most": "Liked most",
        "interest_source": "Interest source",
        "recommendation": "Recommendation",
        "raffle": "Raffle",
        "comments": "Comments",
    }
    for key, label in labels.items():
        if survey.get(key):
            value = survey[key]
            if isinstance(value, list):
                value = ", ".join(value)
            lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def _format_survey_line(survey: dict[str, Any]) -> str:
    liked = ", ".join(survey.get("liked_most", []))
    return (
        f"- #{survey.get('id')} {survey.get('first_name')} {survey.get('last_name')} "
        f"({survey.get('date_of_survey')}): liked {liked}; recommendation {survey.get('recommendation')}"
    )
