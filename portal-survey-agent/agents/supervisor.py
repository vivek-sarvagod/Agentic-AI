"""
agents/supervisor.py
---------------------
The orchestrator. Every user message enters here.

THREE-LAYER ROUTING (cheapest first)
--------------------------------------
Layer 1 — Session state  (0 ms, 0 tokens)
  If there is a pending confirmation (yes/no) or an active create
  draft, we already know which agent to resume. Skip everything else.

Layer 2 — Regex fast-path  (~0 ms, 0 tokens)
  Keyword groups map to agent names with high confidence.
  ~60% of single-intent queries resolve here.

Layer 3 — LLM classification  (~300 ms, ~50 tokens)
  For ambiguous or compound queries.  The LLM returns a JSON list of
  agent names, e.g. ["campus_info", "analytics"].

PARALLEL DISPATCH
-----------------
After planning, all selected agents run concurrently using
asyncio.gather().  This keeps latency at max(slowest_agent) rather
than sum(all_agents).

SYNTHESIS
---------
_synthesize_node() reads all per-agent result keys and assembles:
  - state["response"]    plain text for the chat bubble
  - state["ui_hints"]    structured data the React UI renders
  - state["agent_tags"]  labels shown in the bubble header
  - state["quick_actions"] suggestion buttons
"""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from langgraph.graph import END, StateGraph

from config import settings
from shared.state import AgentName, AgentState
from agents.crud_agent import CrudAgent
from agents.analytics_agent import AnalyticsAgent
from agents.campus_info_agent import CampusInfoAgent
from agents.insight_agent import InsightAgent

# ── Agent display labels shown in the React UI ────────────────────────────────
AGENT_LABELS: dict[AgentName, str] = {
    "crud": "Survey agent",
    "analytics": "Analytics agent",
    "campus_info": "Campus info agent",
    "insight": "Insight agent",
}

# ── Regex keyword groups for fast-path routing ────────────────────────────────
# Campus routing only fires when the query explicitly references an educational institution.
# Generic location words ("where is", "address", "map") are intentionally excluded — they
# match too broadly (e.g. "where is Panera Bread?") and are handled by the intent check below.
CAMPUS_SIGNALS  = r"\b(campus|university|universities|college|colleges|institute|gmu|gwu|gmu\.edu|george\s+mason|george\s+washington|mit|ucla|nyu|stanford|harvard|programs|admissions|ranking)\b"
CRUD_SIGNALS    = r"\b(create|add|new survey|delete|remove|update|change|modify|show survey|list survey|find survey|search survey|get survey|display survey|view survey|all surveys?)\b"
STATS_SIGNALS   = r"\b(how many|count|total|most common|trend|stats|statistics|percentage|breakdown|analytics|overview)\b"
INSIGHT_SIGNALS = r"\b(summarize|summary|sentiment|what do students|what students (say|think|feel)|feedback|overall|patterns|insights?)\b"


class SupervisorAgent:
    def __init__(self) -> None:
        # Instantiate every sub-agent once — they are stateless workers
        self._agents: dict[AgentName, Any] = {
            "crud": CrudAgent(),
            "analytics": AnalyticsAgent(),
            "campus_info": CampusInfoAgent(),
            "insight": InsightAgent(),
        }
        self.graph = self._build_graph()

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self, message: str, session: dict[str, Any]) -> dict[str, Any]:
        """
        Called by main.py for every incoming chat message.
        Returns the final state dict which main.py converts to AgentResponse.
        """
        state: AgentState = {"user_query": message, "session": session}
        result = await self.graph.ainvoke(state)
        # Merge any session mutations back so main.py can persist them
        session.update(result.get("session", {}))
        return result

    # ── Graph construction ────────────────────────────────────────────────────

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("plan", self._plan_node)
        graph.add_node("dispatch", self._dispatch_node)
        graph.add_node("synthesize", self._synthesize_node)

        graph.set_entry_point("plan")
        graph.add_conditional_edges(
            "plan",
            # If response is already set (e.g. cancel) skip dispatch
            lambda s: "synthesize" if s.get("response") else "dispatch",
            {"dispatch": "dispatch", "synthesize": "synthesize"},
        )
        graph.add_edge("dispatch", "synthesize")
        graph.add_edge("synthesize", END)
        return graph.compile()

    # ── Node 1: Plan ──────────────────────────────────────────────────────────

    async def _plan_node(self, state: AgentState) -> AgentState:
        """
        Determine which sub-agents to invoke.
        Uses 3-layer routing: session → regex → LLM.
        """
        session = state.get("session", {})
        query = state.get("user_query", "").strip()
        lower = query.lower()

        # ── Layer 1: session state ─────────────────────────────────────────
        if session.get("pending_action") and lower in {"yes", "y", "confirm", "approve", "do it"}:
            pending = session["pending_action"]
            session["confirmation"] = True
            state["session"] = session
            state["agents_to_invoke"] = [pending]   # type: ignore[list-item]
            return state

        if session.get("pending_action") and lower in {"no", "n", "cancel", "stop"}:
            session.clear()
            state["session"] = session
            state["response"] = "Canceled. No changes were made."
            state["agent_tags"] = []
            state["ui_hints"] = {}
            return state

        if session.get("draft"):
            state["agents_to_invoke"] = ["crud"]
            return state

        # ── Layer 2: regex fast-path ───────────────────────────────────────
        fast = self._regex_route(lower)
        if fast:
            state["agents_to_invoke"] = fast
            return state

        # ── Layer 3: LLM classification ────────────────────────────────────
        state["agents_to_invoke"] = await self._llm_classify(query)
        return state

    def _regex_route(self, lower: str) -> list[AgentName] | None:
        """
        Map keyword signals to a list of agent names.
        Returns None if no signal is confident enough (fall through to LLM).
        
        Priority rules:
        1. Survey analysis (insight, stats) takes precedence over campus info
        2. Campus queries (website, location, programs) for university info only
        3. CRUD operations are checked last
        """
        matched: list[AgentName] = []
        
        # Check all signals
        has_campus = re.search(CAMPUS_SIGNALS, lower)
        has_crud = re.search(CRUD_SIGNALS, lower)
        has_stats = re.search(STATS_SIGNALS, lower)
        has_insight = re.search(INSIGHT_SIGNALS, lower)
        
        # Priority 0: CRUD operations take precedence - don't confuse "address" field with campus location
        # If clear CRUD intent (create/delete/update), ignore campus signals that might come from survey fields
        if has_crud and re.search(r"\b(create|add|delete|remove|update|change|modify|new survey)\b", lower):
            # This is a CRUD operation - "address" is a survey field, not campus query
            matched.append("crud")
            return matched
        
        # Priority 1: Survey sentiment/analysis - exclude campus_info
        # Only when asking about student feelings/opinions, not when explicitly requesting campus info
        if has_insight and re.search(r"\b(students|student)\s+(feel|think|say|opinion)", lower):
            # This is about survey sentiment analysis, not campus facts
            if has_stats:   matched.append("analytics")
            if has_insight: matched.append("insight")
            if has_crud:    matched.append("crud")
            return matched if matched else None
        
        # Priority 2: Pure campus info queries - return ONLY campus_info
        if has_campus and re.search(r"\b(official|website|site|location|address|map|programs|admissions|about|university|college)\b", lower):
            if not re.search(r"\b(survey|surveys)\b", lower):
                # No mention of surveys - pure campus query
                return ["campus_info"]
        
        # Otherwise, include all that match
        if has_campus:  matched.append("campus_info")
        if has_stats:   matched.append("analytics")
        if has_insight: matched.append("insight")
        if has_crud:    matched.append("crud")
        
        return matched if matched else None

    async def _llm_classify(self, query: str) -> list[AgentName]:
        """
        Use the LLM to classify ambiguous queries.
        Returns a validated list of AgentName literals.
        Falls back to ["crud"] on any error.
        """
        if not settings.OPENAI_API_KEY:
            return ["crud"]  # safe default without a key
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0,
                max_tokens=30,  # we only need a short JSON list
            )
            system = (
                'You route user queries to specialist agents for a Student Survey portal.\n'
                'Agents: "crud" (create/read/update/delete surveys), '
                '"analytics" (counts/trends/stats), '
                '"campus_info" (location/maps/official site/programs), '
                '"insight" (LLM sentiment summary of feedback).\n'
                'Return ONLY a JSON array, e.g. ["crud"] or ["campus_info","analytics"].\n'
                'No explanation. No markdown. Just the array.'
            )
            resp = await model.ainvoke([
                SystemMessage(content=system),
                HumanMessage(content=query),
            ])
            raw = str(resp.content).strip()
            agents = json.loads(raw)
            valid: set[AgentName] = {"crud", "analytics", "campus_info", "insight"}
            return [a for a in agents if a in valid] or ["crud"]
        except Exception:
            return ["crud"]

    # ── Node 2: Dispatch ──────────────────────────────────────────────────────

    async def _dispatch_node(self, state: AgentState) -> AgentState:
        """
        Run all selected agents in parallel using asyncio.gather().

        IMPORTANT: Each agent receives a COPY of the state dict.
        This prevents agents from accidentally overwriting each other's keys
        while they run concurrently.

        KEY MAP NOTE
        ------------
        We use an explicit map from agent name → state result key.
        Do NOT use f"{name}_result" — "campus_info" would produce
        "campus_info_result" but the state key is "campus_result".
        """
        agents_to_run = state.get("agents_to_invoke", ["crud"])

        # Explicit map: agent name → the state key each agent writes into
        RESULT_KEY: dict[str, str] = {
            "crud":        "crud_result",
            "analytics":   "analytics_result",
            "campus_info": "campus_result",     # NOT campus_info_result
            "insight":     "insight_result",
        }

        async def run_agent(name: AgentName) -> AgentState:
            agent = self._agents[name]
            # Deep-enough copy: new dict, same nested values
            # Each agent only writes its own top-level result key so this is safe
            agent_state: AgentState = dict(state)  # type: ignore[assignment]
            return await agent.run(agent_state)

        results: list[AgentState] = await asyncio.gather(
            *[run_agent(name) for name in agents_to_run],
            return_exceptions=False,
        )

        # Merge each agent's result key back into the shared state
        for name, result in zip(agents_to_run, results):
            result_key = RESULT_KEY.get(name, f"{name}_result")
            if result_key in result:
                state[result_key] = result[result_key]  # type: ignore[literal-required]

        # If CRUD agent ran, pull session mutations back so main.py can persist them
        if "crud" in agents_to_run:
            crud_result = state.get("crud_result", {})
            if isinstance(crud_result, dict) and crud_result.get("session"):
                state["session"] = crud_result["session"]

        return state

    # ── Node 3: Synthesize ────────────────────────────────────────────────────

    async def _synthesize_node(self, state: AgentState) -> AgentState:
        """
        Combine all agent results into:
          state["response"]     - text shown in the chat bubble
          state["ui_hints"]     - structured data for rich React rendering
          state["agent_tags"]   - coloured labels in the bubble header
          state["quick_actions"] - suggestion buttons
        """
        # If response was already set (cancel / error), pass through
        if state.get("response"):
            return state

        agents_ran = state.get("agents_to_invoke", [])
        parts: list[str] = []
        ui_hints: dict[str, Any] = {
            "show_map": False,
            "show_info_chips": False,
            "show_link_card": False,
            "show_charts": False,
            "chips": [],
            "charts": [],
        }
        quick_actions: list[dict[str, str]] = []
        needs_confirmation = False
        pending_action = None

        # ── CRUD result ────────────────────────────────────────────────────
        if "crud" in agents_ran:
            cr = state.get("crud_result", {})
            if cr.get("response"):
                parts.append(cr["response"])
            if cr.get("requires_confirmation"):
                needs_confirmation = True
                pending_action = cr.get("pending_action")

        # ── Analytics result ───────────────────────────────────────────────
        if "analytics" in agents_ran:
            ar = state.get("analytics_result", {})
            if ar.get("summary"):
                parts.append(ar["summary"])
            if ar.get("charts"):
                ui_hints["show_charts"] = True
                ui_hints["charts"] = ar["charts"]
            if not quick_actions:
                quick_actions += [
                    {"label": "Recommendation breakdown", "prompt": "Show recommendation breakdown"},
                    {"label": "Interest sources", "prompt": "Show interest source breakdown"},
                ]

        # ── Campus info result ─────────────────────────────────────────────
        if "campus_info" in agents_ran:
            # Key is "campus_result" (NOT "campus_info_result")
            campr = state.get("campus_result", {})
            if not isinstance(campr, dict):
                campr = {}
            if campr.get("summary"):
                parts.append(campr["summary"])
            elif campr.get("name"):
                # Fallback: at minimum mention the campus name
                parts.append(f"I found information about {campr['name']}.")
            campus_hints = campr.get("ui_hints", {})
            if isinstance(campus_hints, dict):
                if campus_hints.get("show_map"):
                    ui_hints["show_map"] = True
                    ui_hints["map"] = campus_hints["map"]
                if campus_hints.get("show_info_chips"):
                    ui_hints["show_info_chips"] = True
                    ui_hints["chips"] = campus_hints.get("chips", [])
                if campus_hints.get("show_link_card"):
                    ui_hints["show_link_card"] = True
                    ui_hints["link_card"] = campus_hints.get("link_card", {})
                if campus_hints.get("quick_actions"):
                    quick_actions = campus_hints["quick_actions"]

        # ── Insight result ─────────────────────────────────────────────────
        if "insight" in agents_ran:
            ir = state.get("insight_result", {})
            if ir.get("summary"):
                parts.append(ir["summary"])

        # ── Assemble final state ───────────────────────────────────────────
        if parts:
            state["response"] = "\n\n".join(parts)
        else:
            # Nothing came back — give a useful fallback instead of a blank message
            agent_names = ", ".join(agents_ran) if agents_ran else "none"
            state["response"] = (
                f"I ran the following agent(s): {agent_names}, "
                "but did not receive a usable result. "
                "Please check that portal-survey-api is running and try again."
            )
        state["ui_hints"] = ui_hints
        state["agent_tags"] = [AGENT_LABELS[a] for a in agents_ran if a in AGENT_LABELS]
        state["quick_actions"] = quick_actions
        state["requires_confirmation"] = needs_confirmation
        if pending_action:
            state["pending_action"] = pending_action

        return state